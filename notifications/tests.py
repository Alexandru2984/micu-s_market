import json
from io import StringIO

from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .consumers import NotificationConsumer
from .models import Notification

User = get_user_model()

INMEMORY_LAYER = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


class NotificationEmailTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notify",
            email="notify@example.com",
            password="NotifyPass123!",
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_notification_emails_marks_notification_sent(self):
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type="new_message",
            title="Mesaj nou",
            message="Ai primit un mesaj.",
        )

        output = StringIO()
        call_command("send_notification_emails", stdout=output)

        notification.refresh_from_db()
        self.assertTrue(notification.is_emailed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Emailuri notificări trimise: 1", output.getvalue())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_URL="https://market.example",
    )
    def test_notification_email_uses_site_url_for_relative_action_url(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type="new_message",
            title="Mesaj nou",
            message="Ai primit un mesaj.",
            action_url="/chat/conversation/1/",
        )

        call_command("send_notification_emails")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://market.example/chat/conversation/1/", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_URL="https://market.example",
    )
    def test_notification_email_rejects_external_action_url(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type="new_message",
            title="Mesaj nou",
            message="Ai primit un mesaj.",
            action_url="https://evil.example/phishing",
        )

        call_command("send_notification_emails")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://market.example/", mail.outbox[0].body)
        self.assertNotIn("evil.example", mail.outbox[0].body)


class NotificationViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notify-view",
            email="notify-view@example.com",
            password="NotifyPass123!",
        )

    def test_notification_list_counts_unread_before_limit(self):
        for index in range(55):
            Notification.objects.create(
                recipient=self.user,
                notification_type="system",
                title=f"Notificare {index}",
                message="Mesaj",
                is_read=index < 5,
            )

        self.client.login(username="notify-view", password="NotifyPass123!")
        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["notifications"]), 50)
        self.assertEqual(response.context["unread_count"], 50)


@override_settings(CHANNEL_LAYERS=INMEMORY_LAYER)
class NotificationConsumerTestCase(TransactionTestCase):
    def setUp(self):
        from categories.models import Category
        from chat.models import Conversation
        from listings.models import Listing

        self.user = User.objects.create_user(username="nc_user", email="nc@example.com", password="Pass123!")
        self.other = User.objects.create_user(username="nc_other", email="nco@example.com", password="Pass123!")
        category = Category.objects.create(name="NC", slug="nc", is_active=True)
        listing = Listing.objects.create(
            title="NC", description="t", price=1, owner=self.other, category=category, city="X", status="active",
        )
        self.conv = Conversation.objects.create(listing=listing)
        self.conv.participants.add(self.user, self.other)

    def _communicator(self, user):
        scope = {
            "type": "websocket",
            "path": "/ws/notifications/",
            "headers": [],
            "subprotocols": [],
            "query_string": b"",
            "user": user,
        }
        return ApplicationCommunicator(NotificationConsumer.as_asgi(), scope)

    @staticmethod
    async def _connect(comm):
        await comm.send_input({"type": "websocket.connect"})
        return await comm.receive_output(timeout=5)

    def test_anonymous_is_rejected(self):
        async def run():
            out = await self._connect(self._communicator(AnonymousUser()))
            return out["type"]
        self.assertEqual(async_to_sync(run)(), "websocket.close")

    def test_initial_unread_count_sent_on_connect(self):
        from chat.models import Message
        Message.objects.create(conversation=self.conv, sender=self.other, receiver=self.user, content="salut")

        async def run():
            comm = self._communicator(self.user)
            accept = await self._connect(comm)
            self.assertEqual(accept["type"], "websocket.accept")
            out = await comm.receive_output(timeout=5)
            await comm.send_input({"type": "websocket.disconnect", "code": 1000})
            return json.loads(out["text"])

        data = async_to_sync(run)()
        self.assertEqual(data["type"], "unread")
        self.assertEqual(data["count"], 1)

    def test_live_update_pushed_on_new_message(self):
        from chat.models import Message

        async def run():
            comm = self._communicator(self.user)
            await self._connect(comm)
            await comm.receive_output(timeout=5)  # initial count (0)
            await database_sync_to_async(Message.objects.create)(
                conversation=self.conv, sender=self.other, receiver=self.user, content="nou",
            )
            update = await comm.receive_output(timeout=5)
            await comm.send_input({"type": "websocket.disconnect", "code": 1000})
            return json.loads(update["text"])

        data = async_to_sync(run)()
        self.assertEqual(data["type"], "unread")
        self.assertEqual(data["count"], 1)
