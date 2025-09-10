from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import Listing, ListingImage
from categories.models import Category


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'category', 'price', 'city', 'county', 'location', 'contact_phone', 'condition', 'negotiable']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Introdu titlul anunțului'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descrie produsul sau serviciul tău în detaliu...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preț în RON',
                'step': '0.01',
                'min': '0'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Orașul unde se află produsul'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Județul'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresa completă (opțional)'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numărul tău de telefon (opțional)'
            }),
            'condition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'negotiable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Titlu anunț',
            'description': 'Descriere',
            'category': 'Categorie',
            'price': 'Preț (RON)',
            'city': 'Oraș',
            'county': 'Județ',
            'location': 'Adresă completă',
            'contact_phone': 'Telefon contact',
            'condition': 'Starea produsului',
            'negotiable': 'Preț negociabil'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Toate categoriile active - temporar pentru debugging
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('name')
        
        # Doar câmpurile principale sunt obligatorii
        required_fields = ['title', 'description', 'category', 'price', 'city']
        for field_name, field in self.fields.items():
            if field_name in required_fields:
                field.required = True
            else:
                field.required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise ValidationError('Prețul trebuie să fie mai mare decât 0.')
        if price > 1000000:
            raise ValidationError('Prețul nu poate fi mai mare de 1.000.000 RON.')
        return price

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        # Fără validări - orice text este acceptat
        return phone


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'image': 'Imagine'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Verifică dimensiunea fișierului (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Imaginea nu poate fi mai mare de 5MB.')
            
            # Verifică tipul fișierului
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = image.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Doar fișierele JPG, PNG și WebP sunt acceptate.')
        
        return image


# Formset pentru multiple imagini
from django.forms import modelformset_factory

ListingImageFormSet = modelformset_factory(
    ListingImage,
    form=ListingImageForm,
    extra=3,  # 3 formulare goale în plus
    max_num=10,  # Maximum 10 imagini
    can_delete=True,
    validate_min=False,  # Nu cere imagini obligatorii
    min_num=0  # Minim 0 imagini
)
