from io import StringIO

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Notification

User = get_user_model()


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
        notification = Notification.objects.create(
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
        notification = Notification.objects.create(
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
