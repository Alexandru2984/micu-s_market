"""
Teste pentru sistemul de chat — conversații și mesaje
"""
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Conversation, Message, MessageAttachment
from listings.models import Listing
from categories.models import Category
from notifications.models import Notification

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

    def test_unread_count_requires_get(self):
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.post(reverse('chat:unread_count'))

        self.assertEqual(response.status_code, 405)

    def test_search_users_requires_get(self):
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.post(reverse('chat:search_users'), {'q': 'seller'})

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

    @override_settings(CHAT_MESSAGE_MAX_LENGTH=20)
    def test_send_too_long_message_rejected(self):
        """Mesajele peste limita server-side sunt respinse."""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)

        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.post(
            reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
            {'content': 'x' * 21},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_send_message_creates_receiver_notification(self):
        """Un mesaj nou creează notificare pentru destinatar."""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)

        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.post(
            reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
            {'content': 'Salut'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        notification = Notification.objects.get(recipient=self.seller, notification_type='new_message')
        self.assertEqual(notification.related_object_id, conv.pk)

    def test_send_message_accepts_valid_text_attachment(self):
        """Atașamentele text valide sunt salvate."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                conv = Conversation.objects.create(listing=self.listing)
                conv.participants.add(self.buyer, self.seller)

                self.client.login(username='buyer', password='BuyerPass123!')
                response = self.client.post(
                    reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
                    {
                        'content': 'mesaj cu atasament',
                        'attachments': SimpleUploadedFile(
                            'nota.txt',
                            b'continut valid',
                            content_type='text/plain',
                        ),
                    },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(MessageAttachment.objects.count(), 1)
                self.assertEqual(response.json()['message']['attachments'][0]['filename'], 'nota.txt')

    def test_send_message_skips_spoofed_pdf_attachment(self):
        """Fișierele care doar pretind că sunt PDF sunt ignorate."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                conv = Conversation.objects.create(listing=self.listing)
                conv.participants.add(self.buyer, self.seller)

                self.client.login(username='buyer', password='BuyerPass123!')
                response = self.client.post(
                    reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
                    {
                        'content': 'mesaj cu pdf fals',
                        'attachments': SimpleUploadedFile(
                            'contract.pdf',
                            b'nu este pdf',
                            content_type='application/pdf',
                        ),
                    },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(MessageAttachment.objects.count(), 0)
                self.assertEqual(response.json()['message']['attachments'], [])

    def test_send_message_skips_invalid_image_attachment(self):
        """Imaginile corupte sau false sunt ignorate."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                conv = Conversation.objects.create(listing=self.listing)
                conv.participants.add(self.buyer, self.seller)

                self.client.login(username='buyer', password='BuyerPass123!')
                response = self.client.post(
                    reverse('chat:send_message', kwargs={'conversation_pk': conv.pk}),
                    {
                        'content': 'mesaj cu imagine falsa',
                        'attachments': SimpleUploadedFile(
                            'poza.jpg',
                            b'nu este imagine',
                            content_type='image/jpeg',
                        ),
                    },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(MessageAttachment.objects.count(), 0)
                self.assertEqual(response.json()['message']['attachments'], [])

    def test_attachment_download_allowed_for_participant(self):
        """Participanții conversației pot descărca atașamentele."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                conv = Conversation.objects.create(listing=self.listing)
                conv.participants.add(self.buyer, self.seller)
                message = Message.objects.create(
                    conversation=conv,
                    sender=self.buyer,
                    receiver=self.seller,
                    content='cu atasament',
                )
                attachment = MessageAttachment.objects.create(
                    message=message,
                    file=SimpleUploadedFile('secret.txt', b'secret', content_type='text/plain'),
                )

                self.client.login(username='buyer', password='BuyerPass123!')
                response = self.client.get(
                    reverse('chat:attachment_download', kwargs={'pk': attachment.pk})
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Cache-Control'], 'private, no-store')
                self.assertEqual(response['Pragma'], 'no-cache')
                self.assertEqual(response['X-Content-Type-Options'], 'nosniff')

    def test_attachment_download_denied_for_non_participant(self):
        """Utilizatorii din afara conversației nu pot descărca atașamentele."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                conv = Conversation.objects.create(listing=self.listing)
                conv.participants.add(self.buyer, self.seller)
                message = Message.objects.create(
                    conversation=conv,
                    sender=self.buyer,
                    receiver=self.seller,
                    content='cu atasament',
                )
                attachment = MessageAttachment.objects.create(
                    message=message,
                    file=SimpleUploadedFile('secret.txt', b'secret', content_type='text/plain'),
                )

                self.client.login(username='third', password='ThirdPass123!')
                response = self.client.get(
                    reverse('chat:attachment_download', kwargs={'pk': attachment.pk})
                )
                self.assertEqual(response.status_code, 404)
