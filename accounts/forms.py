from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, UserReport

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Adresa de email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Prenume'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nume de familie'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nume de utilizator'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Parolă'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmă parola'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nume de utilizator sau email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Parolă'
    }))

class UserProfileForm(forms.ModelForm):
    # Câmpuri pentru User
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prenume'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nume de familie'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresa de email'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'phone', 'city', 'county', 'date_of_birth']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_avatar'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Scrie câteva cuvinte despre tine...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numărul tău de telefon'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Orașul unde locuiești'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Județul'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'avatar': 'Poza de profil',
            'bio': 'Despre mine',
            'phone': 'Telefon',
            'city': 'Oraș',
            'county': 'Județ',
            'date_of_birth': 'Data nașterii'
        }

    def __init__(self, *args, **kwargs):
        # Extrage user-ul din kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populează câmpurile User dacă există
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Actualizează câmpurile User
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        return profile

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Verifică dimensiunea fişierului (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Imaginea nu poate fi mai mare de 5MB.')
            
            # Verifică extensia
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = avatar.name.rsplit('.', 1)[-1].lower() if '.' in avatar.name else ''
            if ext not in valid_extensions:
                raise forms.ValidationError('Doar fişierele JPG, PNG şi WebP sunt acceptate.')
            
            # Verifică conținutul real al fişierului cu Pillow
            try:
                from PIL import Image as PilImage
                avatar.seek(0)
                img = PilImage.open(avatar)
                img.verify()
                avatar.seek(0)
            except Exception:
                raise forms.ValidationError('Fişierul nu este o imagine validă.')
        
        return avatar


class UserReportForm(forms.ModelForm):
    class Meta:
        model = UserReport
        fields = ["reason", "details"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-control"}),
            "details": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Descrie pe scurt problema (opțional)",
            }),
        }
        labels = {
            "reason": "Motiv",
            "details": "Detalii",
        }
