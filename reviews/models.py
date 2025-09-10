from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Review(models.Model):
    # Cine scrie review-ul
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given', verbose_name="Recenzor")
    # Pentru cine se scrie review-ul
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', verbose_name="Utilizator recenzat")
    # Anunțul pentru care se face review-ul (opțional)
    listing = models.ForeignKey('listings.Listing', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name="Anunț")
    
    # Conținutul review-ului
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating")
    title = models.CharField(max_length=200, blank=True, verbose_name="Titlu")
    comment = models.TextField(verbose_name="Comentariu")
    
    # Tipul de tranzacție
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Cumpărare'),
        ('sale', 'Vânzare'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name="Tip tranzacție")
    
    # Date și status
    is_approved = models.BooleanField(default=True, verbose_name="Aprobat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Recenzie"
        verbose_name_plural = "Recenzii"
        # Un user poate lăsa un singur review pentru o anumită tranzacție
        unique_together = ['reviewer', 'reviewed_user', 'listing']
    
    def __str__(self):
        return f"Review de la {self.reviewer.username} pentru {self.reviewed_user.username} - {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizează statisticile utilizatorului recenzat
        if hasattr(self.reviewed_user, 'profile'):
            self.reviewed_user.profile.update_statistics()


class ReviewResponse(models.Model):
    """Răspunsul utilizatorului la un review primit"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response', verbose_name="Review")
    response_text = models.TextField(verbose_name="Răspuns")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        verbose_name = "Răspuns la recenzie"
        verbose_name_plural = "Răspunsuri la recenzii"
    
    def __str__(self):
        return f"Răspuns la review-ul {self.review.id}"
