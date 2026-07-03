from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from Micu_market.images import optimize_image_field

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
    
    # Relations
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings", verbose_name="Proprietar", null=True, blank=True)
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name="listings", verbose_name="Categorie")
    
    # Location
    city = models.CharField(max_length=100, default="București", verbose_name="Oraș")
    county = models.CharField(max_length=100, default="București", verbose_name="Județ")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Adresă completă")
    
    # Contact
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon contact")
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    is_featured = models.BooleanField(default=False, verbose_name="Promovat")
    featured_until = models.DateTimeField(null=True, blank=True, verbose_name="Promovat până la")
    views_count = models.IntegerField(default=0, verbose_name="Număr vizualizări")
    risk_score = models.PositiveSmallIntegerField(default=0, verbose_name="Scor risc")
    needs_moderation_review = models.BooleanField(default=False, verbose_name="Necesită moderare")
    moderation_note = models.TextField(blank=True, verbose_name="Notă moderare")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expiră la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Anunț"
        verbose_name_plural = "Anunțuri"
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['status', 'price']),
            models.Index(fields=['status', 'city']),
            models.Index(fields=['status', 'is_featured', 'featured_until', '-created_at']),
            models.Index(fields=['needs_moderation_review', '-created_at']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug uniqueness, excluding the current instance
            original_slug = self.slug
            counter = 1
            while Listing.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('listings:detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_promoted(self):
        if not self.is_featured:
            return False
        return self.featured_until is None or self.featured_until > timezone.now()
    
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
        indexes = [
            models.Index(fields=['listing', 'order']),
        ]
    
    def __str__(self):
        return f"Imagine pentru {self.listing.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            optimized_name = optimize_image_field(self.image, (800, 800), quality=85)
            if optimized_name and optimized_name != self.image.name:
                self.image.name = optimized_name
                type(self).objects.filter(pk=self.pk).update(image=optimized_name)


class ListingTransaction(models.Model):
    """Record of a completed sale for a listing.

    ``buyer`` is one of the users the seller talked to in chat about this
    listing; it stays NULL when the item was sold outside the platform.
    Reviews link to this record so ratings reflect real transactions.
    """

    listing = models.OneToOneField(
        Listing,
        on_delete=models.CASCADE,
        related_name="transaction",
        verbose_name="Anunț",
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Vânzător",
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases",
        verbose_name="Cumpărător",
    )
    sold_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Preț final",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vândut la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tranzacție anunț"
        verbose_name_plural = "Tranzacții anunțuri"
        indexes = [
            models.Index(fields=["seller", "-created_at"]),
            models.Index(fields=["buyer", "-created_at"]),
        ]

    def __str__(self):
        buyer = self.buyer.username if self.buyer else "în afara platformei"
        return f"{self.listing.title} → {buyer}"

    def involves(self, first_user, second_user):
        """True when the two users are exactly the seller/buyer pair."""
        if self.buyer is None:
            return False
        pair = {self.seller_id, self.buyer_id}
        return {first_user.pk, second_user.pk} == pair


class ListingReport(models.Model):
    REASON_CHOICES = [
        ("scam", "Înșelătorie"),
        ("prohibited", "Produs interzis"),
        ("misleading", "Informații false"),
        ("offensive", "Conținut ofensator"),
        ("duplicate", "Anunț duplicat"),
        ("other", "Alt motiv"),
    ]

    STATUS_CHOICES = [
        ("pending", "În așteptare"),
        ("reviewed", "Verificat"),
        ("dismissed", "Respins"),
        ("action_taken", "Acțiune aplicată"),
    ]

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Anunț",
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listing_reports",
        verbose_name="Raportat de",
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, verbose_name="Motiv")
    details = models.TextField(blank=True, verbose_name="Detalii")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Status",
    )
    moderator_note = models.TextField(blank=True, verbose_name="Notă moderator")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Raport anunț"
        verbose_name_plural = "Rapoarte anunțuri"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["listing", "status"]),
            models.Index(fields=["reporter", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_reason_display()} - {self.listing.title}"

    @property
    def is_active(self):
        return self.status in {"pending", "reviewed"}
