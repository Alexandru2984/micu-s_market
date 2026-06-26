"""
Teste pentru sistemul de chat — conversații și mesaje
"""
import asyncio
import json
import tempfile
import zipfile
from io import BytesIO

from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .consumers import ChatConsumer
from .models import Conversation, Message, MessageAttachment
from .validators import is_allowed_chat_attachment
from listings.models import Listing
from categories.models import Category
from notifications.models import Notification

User = get_user_model()

INMEMORY_LAYER = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


class ChatConversationTestCase(TestCase):
    """Tests for conversation access control"""

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
        """Starting a conversation requires authentication"""
        response = self.client.post(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_start_conversation_requires_post(self):
        """Starting a conversation does not accept GET"""
        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.get(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Conversation.objects.exists())

    def test_cannot_start_conversation_with_self(self):
        """The seller cannot start a conversation with themselves"""
        self.client.login(username='seller', password='SellerPass123!')
        response = self.client.post(
            reverse('chat:start_conversation', kwargs={'listing_slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 302)
        # No conversation must be created
        self.assertFalse(Conversation.objects.exists())

    def test_mark_conversation_read_requires_post(self):
        """The separate mark-as-read endpoint does not accept GET"""
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

    def test_conversation_page_renders_for_participant(self):
        """The conversation page renders correctly for a participant."""
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)
        Message.objects.create(conversation=conv, sender=self.seller, receiver=self.buyer, content='Salut!')

        self.client.login(username='buyer', password='BuyerPass123!')
        response = self.client.get(reverse('chat:conversation', kwargs={'pk': conv.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-conversation-id')
        self.assertContains(response, 'chat-conversation__messages')

    def test_third_user_cannot_access_conversation(self):
        """A third-party user cannot access others' conversation"""
        # Create the conversation between buyer and seller
        conv = Conversation.objects.create(listing=self.listing)
        conv.participants.add(self.buyer, self.seller)
        
        # The third user tries to access it
        self.client.login(username='third', password='ThirdPass123!')
        response = self.client.get(
            reverse('chat:conversation', kwargs={'pk': conv.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_inbox_requires_login(self):
        """The inbox requires authentication"""
        response = self.client.get(reverse('chat:inbox'))
        self.assertEqual(response.status_code, 302)

    def test_send_message_requires_post(self):
        """Sending messages requires POST"""
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
        """A new message creates a notification for the recipient."""
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
        """Valid text attachments are saved."""
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
        """Files that only pretend to be PDFs are ignored."""
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

    def test_office_attachment_with_too_many_zip_members_is_rejected(self):
        """Office archives with excessive member counts are rejected."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types></Types>")
            archive.writestr("word/document.xml", "<document></document>")
            for index in range(1001):
                archive.writestr(f"word/extra-{index}.xml", "")
        buffer.seek(0)

        uploaded = SimpleUploadedFile(
            "many-files.docx",
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertFalse(is_allowed_chat_attachment(uploaded))

    def test_attachment_download_allowed_for_participant(self):
        """Conversation participants can download the attachments."""
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
        """Users outside the conversation cannot download the attachments."""
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


@override_settings(CHANNEL_LAYERS=INMEMORY_LAYER)
class ChatConsumerTestCase(TransactionTestCase):
    """Tests for the WebSocket consumer (real-time chat)."""

    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(username='ws_buyer', email='wsb@example.com', password='WsBuyer123!')
        self.seller = User.objects.create_user(username='ws_seller', email='wss@example.com', password='WsSeller123!')
        self.outsider = User.objects.create_user(username='ws_out', email='wso@example.com', password='WsOut123!')
        self.category = Category.objects.create(name='WS Cat', slug='ws-cat', is_active=True)
        self.listing = Listing.objects.create(
            title='Produs WS', description='Test', price=100.00,
            owner=self.seller, category=self.category, city='Cluj', status='active',
        )
        self.conv = Conversation.objects.create(listing=self.listing)
        self.conv.participants.add(self.buyer, self.seller)

    def _communicator(self, user):
        scope = {
            "type": "websocket",
            "path": f"/ws/chat/{self.conv.pk}/",
            "headers": [],
            "subprotocols": [],
            "query_string": b"",
            "user": user,
            "url_route": {"kwargs": {"pk": self.conv.pk}},
        }
        return ApplicationCommunicator(ChatConsumer.as_asgi(), scope)

    @staticmethod
    async def _connect(comm):
        await comm.send_input({"type": "websocket.connect"})
        out = await comm.receive_output(timeout=5)
        return out["type"] == "websocket.accept"

    @staticmethod
    async def _close(comm):
        await comm.send_input({"type": "websocket.disconnect", "code": 1000})

    def test_non_participant_is_rejected(self):
        async def run():
            comm = self._communicator(self.outsider)
            return await self._connect(comm)
        self.assertFalse(async_to_sync(run)())

    def test_anonymous_is_rejected(self):
        async def run():
            comm = self._communicator(AnonymousUser())
            return await self._connect(comm)
        self.assertFalse(async_to_sync(run)())

    def test_message_delivered_live_to_other_participant(self):
        async def run():
            buyer_comm = self._communicator(self.buyer)
            seller_comm = self._communicator(self.seller)
            self.assertTrue(await self._connect(buyer_comm))
            self.assertTrue(await self._connect(seller_comm))
            await buyer_comm.send_input(
                {"type": "websocket.receive", "text": json.dumps({"type": "message", "content": "salut prin websocket"})}
            )
            # The seller (the other party) receives the message live, without a reload.
            received = None
            for _ in range(5):
                out = await seller_comm.receive_output(timeout=5)
                payload = json.loads(out.get("text", "{}")) if out.get("type") == "websocket.send" else {}
                if payload.get("type") == "message":
                    received = payload
                    break
            await self._close(buyer_comm)
            await self._close(seller_comm)
            return received
        received = async_to_sync(run)()
        self.assertIsNotNone(received)
        self.assertEqual(received["message"]["content"], "salut prin websocket")
        self.assertEqual(received["message"]["sender"], "ws_buyer")
        # Persisted in the DB + notification for the recipient.
        self.assertTrue(Message.objects.filter(conversation=self.conv, content="salut prin websocket").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.seller, notification_type="new_message").exists())

    @override_settings(CHAT_WS_MESSAGE_RATE_PER_MINUTE=1)
    def test_websocket_message_rate_limit_is_enforced_across_connection(self):
        async def run():
            comm = self._communicator(self.buyer)
            self.assertTrue(await self._connect(comm))
            await comm.send_input(
                {"type": "websocket.receive", "text": json.dumps({"type": "message", "content": "primul mesaj"})}
            )

            first_received = None
            for _ in range(5):
                out = await comm.receive_output(timeout=5)
                payload = json.loads(out.get("text", "{}")) if out.get("type") == "websocket.send" else {}
                if payload.get("type") == "message":
                    first_received = payload
                    break
            self.assertIsNotNone(first_received)

            await asyncio.sleep(0.35)
            await comm.send_input(
                {"type": "websocket.receive", "text": json.dumps({"type": "message", "content": "al doilea mesaj"})}
            )

            limited = None
            for _ in range(5):
                out = await comm.receive_output(timeout=5)
                payload = json.loads(out.get("text", "{}")) if out.get("type") == "websocket.send" else {}
                if payload.get("type") == "error":
                    limited = payload
                    break
            await self._close(comm)
            return limited

        limited = async_to_sync(run)()
        self.assertEqual(limited, {"type": "error", "code": "rate_limited"})
        self.assertTrue(Message.objects.filter(conversation=self.conv, content="primul mesaj").exists())
        self.assertFalse(Message.objects.filter(conversation=self.conv, content="al doilea mesaj").exists())
