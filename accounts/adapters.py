# accounts/adapters.py
import re

from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User


class CustomAccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):
        """
        Generate a unique username from the email
        """
        # Extract the local part of the email
        if txts:
            email_part = txts[0].split('@')[0]
            # Strip special characters
            username = re.sub(r'[^a-zA-Z0-9._-]', '', email_part)
            username = username[:30]  # Limit to 30 characters

            # Check whether it already exists
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                if len(username) > 30:
                    username = f"{original_username[:25]}{counter}"
            
            return username
        
        # Fall back to the default method
        return super().generate_unique_username(txts, regex)

    def populate_username(self, request, user):
        """
        Populate the username for a new user
        """
        if hasattr(user, 'email') and user.email:
            username = self.generate_unique_username([user.email])
            user.username = username
