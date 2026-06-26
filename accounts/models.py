from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from Micu_market.images import optimize_image_field

User = get_user_model()

class UserProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("unverified", "Neverificat"),
        ("pending", "În verificare"),
        ("verified", "Verificat"),
        ("rejected", "Respins"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Descriere")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    city = models.CharField(max_length=100, blank=True, verbose_name="Oraș")
    county = models.CharField(max_length=100, blank=True, verbose_name="Județ")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data nașterii")
    is_verified = models.BooleanField(default=False, verbose_name="Verificat")
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="unverified",
        verbose_name="Status verificare",
    )
    verification_token = models.CharField(max_length=100, blank=True)
    verification_requested_at = models.DateTimeField(null=True, blank=True, verbose_name="Verificare cerută la")
    verification_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Verificare analizată la")
    verification_note = models.TextField(blank=True, verbose_name="Notă verificare")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistics
    total_listings = models.IntegerField(default=0, verbose_name="Total anunțuri")
    total_sales = models.IntegerField(default=0, verbose_name="Total vânzări")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name="Rating mediu")
    
    class Meta:
        verbose_name = "Profil utilizator"
        verbose_name_plural = "Profile utilizatori"
    
    def __str__(self):
        return f"Profil - {self.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar:
            optimized_name = optimize_image_field(self.avatar, (300, 300), quality=90)
            if optimized_name and optimized_name != self.avatar.name:
                self.avatar.name = optimized_name
                type(self).objects.filter(pk=self.pk).update(avatar=optimized_name)
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.user.username})
    
    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    def request_verification(self):
        if self.is_verified or self.verification_status == "pending":
            return False
        self.verification_status = "pending"
        self.verification_requested_at = timezone.now()
        self.verification_reviewed_at = None
        self.verification_note = ""
        self.save(update_fields=[
            "verification_status",
            "verification_requested_at",
            "verification_reviewed_at",
            "verification_note",
            "updated_at",
        ])
        return True

    def approve_verification(self):
        self.is_verified = True
        self.verification_status = "verified"
        self.verification_reviewed_at = timezone.now()
        self.save(update_fields=["is_verified", "verification_status", "verification_reviewed_at", "updated_at"])

    def reject_verification(self, note=""):
        self.is_verified = False
        self.verification_status = "rejected"
        self.verification_reviewed_at = timezone.now()
        self.verification_note = note
        self.save(update_fields=[
            "is_verified",
            "verification_status",
            "verification_reviewed_at",
            "verification_note",
            "updated_at",
        ])
    
    def update_statistics(self):
        """Update the user's statistics — SQL queries, not Python loops"""
        from listings.models import Listing
        from reviews.models import Review
        from django.db.models import Avg

        # Count active and sold listings
        self.total_listings = Listing.objects.filter(owner=self.user, status='active').count()
        self.total_sales = Listing.objects.filter(owner=self.user, status='sold').count()

        # Average rating — SQL Avg, not sum() in Python
        result = Review.objects.filter(
            reviewed_user=self.user,
            is_approved=True
        ).aggregate(avg=Avg('rating'))
        self.average_rating = round(result['avg'] or 0, 2)

        self.save(update_fields=['total_listings', 'total_sales', 'average_rating'])


# Signal that automatically creates a profile when a new user is created
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create the profile and preferences on the user's first save"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Note: NotificationPreference is created by the notifications/models.py signal


def _update_profile_stats(user):
    """Helper: update the profile statistics if a profile exists"""
    try:
        user.profile.update_statistics()
    except UserProfile.DoesNotExist:
        pass


class UserReport(models.Model):
    REASON_CHOICES = [
        ("scam", "Înșelătorie"),
        ("harassment", "Hărțuire"),
        ("fake_profile", "Profil fals"),
        ("spam", "Spam"),
        ("other", "Alt motiv"),
    ]

    STATUS_CHOICES = [
        ("pending", "În așteptare"),
        ("reviewed", "Verificat"),
        ("dismissed", "Respins"),
        ("action_taken", "Acțiune aplicată"),
    ]

    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_received", verbose_name="Utilizator raportat")
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_reports_made", verbose_name="Raportat de")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, verbose_name="Motiv")
    details = models.TextField(blank=True, verbose_name="Detalii")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Status")
    moderator_note = models.TextField(blank=True, verbose_name="Notă moderator")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Raport utilizator"
        verbose_name_plural = "Rapoarte utilizatori"
        indexes = [
            models.Index(fields=["reported_user", "status"]),
            models.Index(fields=["reporter", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_reason_display()} - {self.reported_user.username}"


class UserStrike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="strikes", verbose_name="Utilizator")
    reason = models.CharField(max_length=200, verbose_name="Motiv")
    notes = models.TextField(blank=True, verbose_name="Note")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="strikes_created", verbose_name="Creat de")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Strike utilizator"
        verbose_name_plural = "Strike-uri utilizatori"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"Strike pentru {self.user.username}: {self.reason}"
