from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    EVENT_TYPES = [
        ("auth.login", "Login"),
        ("auth.logout", "Logout"),
        ("listing.report", "Raport anunț"),
        ("listing.risk_review_required", "Anunț trimis automat la moderare"),
        ("listing.moderation_approved", "Moderare anunț aprobată"),
        ("listing.moderation_requested", "Anunț trimis la moderare"),
        ("listing.promotion_started", "Promovare anunț pornită"),
        ("listing.promotion_stopped", "Promovare anunț oprită"),
        ("profile.verification_requested", "Cerere verificare profil"),
        ("profile.verification_approved", "Verificare profil aprobată"),
        ("profile.verification_rejected", "Verificare profil respinsă"),
        ("system", "Sistem"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Actor",
    )
    event_type = models.CharField(max_length=80, choices=EVENT_TYPES, verbose_name="Tip eveniment")
    object_type = models.CharField(max_length=80, blank=True, verbose_name="Tip obiect")
    object_id = models.CharField(max_length=80, blank=True, verbose_name="ID obiect")
    request_id = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="Request ID")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, verbose_name="User agent")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Creat la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Eveniment audit"
        verbose_name_plural = "Evenimente audit"
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
