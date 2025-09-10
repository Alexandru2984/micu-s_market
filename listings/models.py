from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image
import os

User = get_user_model()

class Listing(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activ'),
        ('sold', 'Vândut'),
        ('reserved', 'Rezervat'),
        ('inactive', 'Inactiv'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Nou'),
        ('like_new', 'Ca nou'),
        ('good', 'Bună stare'),
        ('fair', 'Stare acceptabilă'),
        ('poor', 'Stare proastă'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titlu")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name="Descriere")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preț")
    negotiable = models.BooleanField(default=True, verbose_name="Negociabil")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', verbose_name="Stare")
    
    # Relații
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings", verbose_name="Proprietar", null=True, blank=True)
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name="listings", verbose_name="Categorie")
    
    # Locație
    city = models.CharField(max_length=100, default="București", verbose_name="Oraș")
    county = models.CharField(max_length=100, default="București", verbose_name="Județ")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Adresă completă")
    
    # Contact
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon contact")
    
    # Status și date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    is_featured = models.BooleanField(default=False, verbose_name="Promovat")
    views_count = models.IntegerField(default=0, verbose_name="Număr vizualizări")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expiră la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Anunț"
        verbose_name_plural = "Anunțuri"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Asigură unicitatea slug-ului
            original_slug = self.slug
            counter = 1
            while Listing.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('listings:listing_detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def main_image(self):
        first_image = self.images.first()
        return first_image.image if first_image else None


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images', verbose_name="Anunț")
    image = models.ImageField(upload_to='listings/', verbose_name="Imagine")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Text alternativ")
    order = models.IntegerField(default=0, verbose_name="Ordine")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Imagine anunț"
        verbose_name_plural = "Imagini anunțuri"
    
    def __str__(self):
        return f"Imagine pentru {self.listing.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Redimensionează imaginea pentru optimizare
        if self.image:
            img_path = self.image.path
            with Image.open(img_path) as img:
                # Păstrează raportul de aspect, dar nu mai mare de 800x800
                if img.height > 800 or img.width > 800:
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    img.save(img_path, optimize=True, quality=85)
