from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

class Notification(models.Model):
    """The user notifications system"""
    
    NOTIFICATION_TYPES = [
        ('new_message', 'Mesaj nou'),
        ('new_review', 'Recenzie nouă'),
        ('listing_sold', 'Anunț vândut'),
        ('listing_expired', 'Anunț expirat'),
        ('listing_approved', 'Anunț aprobat'),
        ('listing_rejected', 'Anunț respins'),
        ('price_alert', 'Alertă preț'),
        ('new_listing_in_category', 'Anunț nou în categorie'),
        ('account_verification', 'Verificare cont'),
        ('system', 'Notificare sistem'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Destinatar")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, verbose_name="Tip notificare")
    title = models.CharField(max_length=200, verbose_name="Titlu")
    message = models.TextField(verbose_name="Mesaj")
    
    # Link to the relevant object (optional)
    related_object_type = models.CharField(max_length=50, blank=True, verbose_name="Tip obiect")
    related_object_id = models.IntegerField(null=True, blank=True, verbose_name="ID obiect")
    action_url = models.URLField(blank=True, verbose_name="URL acțiune")
    
    # Status
    is_read = models.BooleanField(default=False, verbose_name="Citit")
    is_emailed = models.BooleanField(default=False, verbose_name="Trimis pe email")
    
    # Date
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Citit la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificare"
        verbose_name_plural = "Notificări"
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_emailed', 'created_at']),
        ]
    
    def __str__(self):
        return f"Notificare pentru {self.recipient.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark the notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()  # fix: models.timezone does not exist
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences', verbose_name="Utilizator")

    # Email preferences
    email_new_messages = models.BooleanField(default=True, verbose_name="Email pentru mesaje noi")
    email_new_reviews = models.BooleanField(default=True, verbose_name="Email pentru recenzii noi")
    email_listing_updates = models.BooleanField(default=True, verbose_name="Email pentru actualizări anunțuri")
    email_price_alerts = models.BooleanField(default=True, verbose_name="Email pentru alerte preț")
    email_marketing = models.BooleanField(default=False, verbose_name="Email marketing")
    
    # In-app notification preferences
    app_new_messages = models.BooleanField(default=True, verbose_name="Notificare aplicație pentru mesaje")
    app_new_reviews = models.BooleanField(default=True, verbose_name="Notificare aplicație pentru recenzii")
    app_listing_updates = models.BooleanField(default=True, verbose_name="Notificare aplicație pentru anunțuri")
    app_system_updates = models.BooleanField(default=True, verbose_name="Notificare aplicație pentru sistem")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferință notificare"
        verbose_name_plural = "Preferințe notificări"
    
    def __str__(self):
        return f"Preferințe notificări - {self.user.username}"


# Signal that creates notification preferences for new users
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(user=instance)
