# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
import re


class CustomAccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):
        """
        Generează un username unic din email
        """
        # Extrage partea din față a emailului
        if txts:
            email_part = txts[0].split('@')[0]
            # Curăță caractere speciale
            username = re.sub(r'[^a-zA-Z0-9._-]', '', email_part)
            username = username[:30]  # Limitează la 30 caractere
            
            # Verifică dacă există deja
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                if len(username) > 30:
                    username = f"{original_username[:25]}{counter}"
            
            return username
        
        # Fallback la metoda default
        return super().generate_unique_username(txts, regex)
    
    def populate_username(self, request, user):
        """
        Populează username-ul pentru user nou
        """
        if hasattr(user, 'email') and user.email:
            username = self.generate_unique_username([user.email])
            user.username = username
