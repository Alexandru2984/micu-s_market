from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

User = get_user_model()

class Review(models.Model):
    # Who writes the review
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given', verbose_name="Recenzor")
    # Who the review is about
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', verbose_name="Utilizator recenzat")
    # The listing the review is about (optional)
    listing = models.ForeignKey('listings.Listing', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name="Anunț")
    # The confirmed sale this review is based on (set automatically when the
    # listing was marked sold to a buyer and the reviewer is part of the pair)
    transaction = models.ForeignKey(
        'listings.ListingTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name="Tranzacție",
    )

    # The review content
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating")
    title = models.CharField(max_length=200, blank=True, verbose_name="Titlu")
    comment = models.TextField(verbose_name="Comentariu")

    # Transaction type
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Cumpărare'),
        ('sale', 'Vânzare'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name="Tip tranzacție")
    
    # Dates and status
    is_approved = models.BooleanField(default=True, verbose_name="Aprobat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Recenzie"
        verbose_name_plural = "Recenzii"
        # A user can leave only one review per transaction
        unique_together = ['reviewer', 'reviewed_user', 'listing']
    
    def __str__(self):
        return f"Review de la {self.reviewer.username} pentru {self.reviewed_user.username} - {self.rating}★"

    @property
    def is_verified_transaction(self):
        return self.transaction_id is not None
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the reviewed user's statistics
        if hasattr(self.reviewed_user, 'profile'):
            self.reviewed_user.profile.update_statistics()


class ReviewResponse(models.Model):
    """The user's response to a received review"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response', verbose_name="Review")
    response_text = models.TextField(verbose_name="Răspuns")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        verbose_name = "Răspuns la recenzie"
        verbose_name_plural = "Răspunsuri la recenzii"
    
    def __str__(self):
        return f"Răspuns la review-ul {self.review.id}"


@receiver(post_delete, sender=Review)
def update_reviewed_user_rating_after_delete(sender, instance, **kwargs):
    if hasattr(instance.reviewed_user, 'profile'):
        instance.reviewed_user.profile.update_statistics()
