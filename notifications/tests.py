from io import StringIO

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

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
