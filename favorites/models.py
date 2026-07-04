from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Utilizator")
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Anunț")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Adăugat la")
    
    class Meta:
        unique_together = ['user', 'listing']  # A user cannot favorite the same listing more than once
        ordering = ['-created_at']
        verbose_name = "Favorit"
        verbose_name_plural = "Favorite"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['listing', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.listing.title}"


class SavedSearch(models.Model):
    """Searches saved by users for notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches', verbose_name="Utilizator")
    name = models.CharField(max_length=100, verbose_name="Nume căutare")
    search_query = models.CharField(max_length=200, blank=True, verbose_name="Termen căutare")
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categorie")
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Preț minim")
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Preț maxim")
    city = models.CharField(max_length=100, blank=True, verbose_name="Oraș")
    county = models.CharField(max_length=100, blank=True, verbose_name="Județ")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    email_notifications = models.BooleanField(default=True, verbose_name="Notificări email")
    # Watermark for the alerts job: only listings created after this moment
    # are reported, so each match is notified exactly once.
    last_checked_at = models.DateTimeField(default=timezone.now, verbose_name="Verificat ultima dată")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Căutare salvată"
        verbose_name_plural = "Căutări salvate"
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', 'email_notifications']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_search_params(self):
        """Return the search parameters as a dictionary"""
        params = {}
        if self.search_query:
            params['q'] = self.search_query
        if self.category:
            params['category'] = self.category.id
        if self.min_price:
            params['min_price'] = self.min_price
        if self.max_price:
            params['max_price'] = self.max_price
        if self.city:
            params['city'] = self.city
        if self.county:
            params['county'] = self.county
        return params
