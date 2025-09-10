from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Utilizator")
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Anunț")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Adăugat la")
    
    class Meta:
        unique_together = ['user', 'listing']  # Un user nu poate adăuga același anunț de mai multe ori la favorite
        ordering = ['-created_at']
        verbose_name = "Favorit"
        verbose_name_plural = "Favorite"
    
    def __str__(self):
        return f"{self.user.username} - {self.listing.title}"


class SavedSearch(models.Model):
    """Căutări salvate de utilizatori pentru notificări"""
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Căutare salvată"
        verbose_name_plural = "Căutări salvate"
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_search_params(self):
        """Returnează parametrii de căutare ca dicționar"""
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
