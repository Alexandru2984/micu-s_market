from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image
import os

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Descriere")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    city = models.CharField(max_length=100, blank=True, verbose_name="Oraș")
    county = models.CharField(max_length=100, blank=True, verbose_name="Județ")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data nașterii")
    is_verified = models.BooleanField(default=False, verbose_name="Verificat")
    verification_token = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistici
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
        
        # Redimensionează avatarul
        if self.avatar:
            img_path = self.avatar.path
            with Image.open(img_path) as img:
                if img.height > 300 or img.width > 300:
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    img.save(img_path, optimize=True, quality=90)
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.user.username})
    
    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username
    
    def update_statistics(self):
        """Actualizează statisticile utilizatorului — query-uri SQL, nu Python loops"""
        from listings.models import Listing
        from reviews.models import Review
        from django.db.models import Avg

        # Contorizare anunțuri active și vândute
        self.total_listings = Listing.objects.filter(owner=self.user, status='active').count()
        self.total_sales = Listing.objects.filter(owner=self.user, status='sold').count()

        # Rating mediu — Avg SQL, nu sum() în Python
        result = Review.objects.filter(
            reviewed_user=self.user,
            is_approved=True
        ).aggregate(avg=Avg('rating'))
        self.average_rating = round(result['avg'] or 0, 2)

        self.save(update_fields=['total_listings', 'total_sales', 'average_rating'])


# Signal pentru a crea automat un profil când se creează un user nou
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Creează profilul şi preferințele la primul save al user-ului"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Notă: NotificationPreference e creat din notifications/models.py signal


def _update_profile_stats(user):
    """Helper: actualizează statisticile profilului dacă există"""
    try:
        user.profile.update_statistics()
    except UserProfile.DoesNotExist:
        pass
