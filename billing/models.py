from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class PromotionPlan(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume")
    days = models.PositiveIntegerField(verbose_name="Zile promovare")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preț")
    currency = models.CharField(max_length=3, default="RON", verbose_name="Monedă")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price", "days"]
        verbose_name = "Plan promovare"
        verbose_name_plural = "Planuri promovare"

    def __str__(self):
        return f"{self.name} - {self.days} zile"


class PromotionOrder(models.Model):
    STATUS_CHOICES = [
        ("pending", "În așteptare"),
        ("paid", "Plătită"),
        ("applied", "Aplicată"),
        ("cancelled", "Anulată"),
    ]

    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE, related_name="promotion_orders", verbose_name="Anunț")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="promotion_orders", verbose_name="Utilizator")
    plan = models.ForeignKey(PromotionPlan, on_delete=models.PROTECT, related_name="orders", verbose_name="Plan")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Status")
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Sumă")
    currency = models.CharField(max_length=3, default="RON", verbose_name="Monedă")
    external_reference = models.CharField(max_length=120, blank=True, verbose_name="Referință externă")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comandă promovare"
        verbose_name_plural = "Comenzi promovare"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.listing.title} - {self.plan.name} ({self.status})"

    def mark_paid(self):
        if self.status == "pending":
            self.status = "paid"
            self.paid_at = timezone.now()
            self.save(update_fields=["status", "paid_at"])

    def apply_promotion(self):
        if self.status not in {"paid", "pending"}:
            return False
        now = timezone.now()
        current_until = self.listing.featured_until if self.listing.is_promoted else now
        self.listing.is_featured = True
        self.listing.featured_until = max(current_until or now, now) + timedelta(days=self.plan.days)
        self.listing.save(update_fields=["is_featured", "featured_until", "updated_at"])
        self.status = "applied"
        if self.paid_at is None:
            self.paid_at = now
        self.applied_at = now
        self.save(update_fields=["status", "paid_at", "applied_at"])
        return True
