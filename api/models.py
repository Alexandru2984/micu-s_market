import hashlib
import hmac
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class ApiKey(models.Model):
    """Personal API key for the public /api/v1/ endpoints.

    The raw key has the shape ``mk_<prefix>_<secret>`` and is shown to the
    user exactly once, at creation. Only a SHA-256 hash is stored; lookups
    go through the short unique prefix.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="Utilizator",
    )
    name = models.CharField(max_length=100, blank=True, verbose_name="Nume")
    prefix = models.CharField(max_length=16, unique=True, verbose_name="Prefix")
    hashed_key = models.CharField(max_length=64, verbose_name="Hash cheie")
    is_active = models.BooleanField(default=True, verbose_name="Activă")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creată la")
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name="Folosită ultima dată")
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="Revocată la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cheie API"
        verbose_name_plural = "Chei API"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name or 'cheie'} ({self.prefix}…) - {self.user.username}"

    @staticmethod
    def _hash(raw_key):
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def generate(cls, user, name=""):
        """Create a key for ``user`` and return ``(instance, raw_key)``."""
        prefix = secrets.token_hex(4)
        secret = secrets.token_urlsafe(32)
        raw_key = f"mk_{prefix}_{secret}"
        instance = cls.objects.create(
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=cls._hash(raw_key),
        )
        return instance, raw_key

    @classmethod
    def authenticate_key(cls, raw_key):
        """Return the owning user for a valid, active raw key; None otherwise."""
        if not raw_key or not raw_key.startswith("mk_"):
            return None
        parts = raw_key.split("_", 2)
        if len(parts) != 3 or not parts[1] or not parts[2]:
            return None

        try:
            key = cls.objects.select_related("user").get(prefix=parts[1], is_active=True)
        except cls.DoesNotExist:
            return None

        if not hmac.compare_digest(key.hashed_key, cls._hash(raw_key)):
            return None
        if not key.user.is_active:
            return None

        cls.objects.filter(pk=key.pk).update(last_used_at=timezone.now())
        return key.user

    def revoke(self):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])
