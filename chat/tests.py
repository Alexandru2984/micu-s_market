"""
Teste pentru sistemul de chat — conversații și mesaje
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from listings.models import Listing
from categories.models import Category

User = get_user_model()


class ChatConversationTestCase(TestCase):
    """Teste pentru access control conversații"""

    def setUp(self):
        self.client = Client()
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='BuyerPass123!'
        )
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='SellerPass123!'
        )
        self.third_user = User.objects.create_user(
            username='third',
            email='third@example.com',
            password='ThirdPass123!'
        )
        self.category = Category.objects.create(
            name='Chat Test Cat',
            slug='chat-test-cat',
            is_active=True
        )
        self.listing = Listing.objects.create(
            title='Produs de test chat',
            description='Test',
            price=200.00,
            owner=self.seller,
            category=self.category,
            city='Timișoara',
            status='active'
        )

    def test_start_conversation_requires_login(self):
        """Pornirea unei conversații necesită autentificare"""
        response = self.client.post(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_start_conversation_requires_post(self):
        """Pornirea unei conversații nu acceptă GET"""
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.get(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Conversation.objects.exists())

    def test_cannot_start_conversation_with_self(self):
        """Vânzătorul nu poate porni o conversație cu sine însuși"""
        self.client.login(username='seller', password='SellerPass123!')
        response = self.client.post(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 302)
        # Nu trebuie creată nicio conversație
        self.assertFalse(Conversation.objects.exists())

    def test_mark_conversation_read_requires_post(self):
        """Endpointul separat de marcare ca citit nu acceptă GET"""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)

        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.get(
            reverse('chat:mark_read', kwargs={'pk': conv.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_third_user_cannot_access_conversation(self):
        """Un utilizator terț nu poate accesa conversația altora"""
        # Creează conversația între buyer și seller
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)
        
        # Third user încearcă să acceseze
        self.client.login(username='third', password='ThirdPass123!')
        response = self.client.get(
            reverse('chat:conversation', kwargs={'pk': conv.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_inbox_requires_login(self):
        """Inbox necesită autentificare"""
        response = self.client.get(reverse('chat:inbox'))
        self.assertEqual(response.status_code, 302)

    def test_send_message_requires_post(self):
        """Trimiterea de mesaje necesită POST"""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)
        
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.get(
            reverse('chat:send_message', kwargs={'conversation_pk': conv.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_send_empty_message_rejected(self):
        """Mesajele goale sunt respinse"""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)
        
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.post(
            reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
            {'content': '   '},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
