from django import forms
from .models import Review, ReviewResponse

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment', 'transaction_type']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} stele') for i in range(1, 6)], attrs={
                'class': 'form-select',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titlul review-ului (opțional)',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Descrie experiența ta cu acest utilizator...',
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'rating': 'Rating',
            'title': 'Titlu (opțional)',
            'comment': 'Comentariu',
            'transaction_type': 'Tip tranzacție',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['rating'].widget.attrs.update({'required': True})

class ReviewResponseForm(forms.ModelForm):
    class Meta:
        model = ReviewResponse
        fields = ['response_text']
        widgets = {
            'response_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Răspunsul tău la acest review...',
            }),
        }
        labels = {
            'response_text': 'Răspuns',
        }

class ReviewFilterForm(forms.Form):
    RATING_CHOICES = [
        ('', 'Toate rating-urile'),
        ('5', '5 stele'),
        ('4', '4 stele'),
        ('3', '3 stele'),
        ('2', '2 stele'),
        ('1', '1 stea'),
    ]
    
    TRANSACTION_CHOICES = [
        ('', 'Toate tipurile'),
        ('purchase', 'Cumpărare'),
        ('sale', 'Vânzare'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Caută în review-uri...'
        })
    )
