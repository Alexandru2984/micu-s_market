from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from notifications.models import Notification

from .models import BackgroundJob

User = get_user_model()


class BackgroundJobTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="job-user",
            email="job@example.com",
            password="JobPass123!",
        )

    def test_enqueue_job_command_creates_known_job(self):
        out = StringIO()

        call_command(
            "enqueue_job",
            "notifications.send_pending_emails",
            "--payload",
            '{"limit": 5}',
            stdout=out,
        )

        job = BackgroundJob.objects.get()
        self.assertEqual(job.name, "notifications.send_pending_emails")
        self.assertEqual(job.payload["limit"], 5)
        self.assertIn("Job queued:", out.getvalue())

    def test_enqueue_job_rejects_unknown_handler(self):
        with self.assertRaises(CommandError):
            call_command("enqueue_job", "missing.handler", stdout=StringIO(), stderr=StringIO())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_run_jobs_sends_pending_notification_email(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type="new_message",
            title="Mesaj nou",
            message="Ai primit un mesaj.",
        )
        BackgroundJob.enqueue("notifications.send_pending_emails", {"limit": 10})

        out = StringIO()
        call_command("run_jobs", "--limit", "1", stdout=out)

        job = BackgroundJob.objects.get()
        notification = Notification.objects.get()
        self.assertEqual(job.status, BackgroundJob.STATUS_SUCCEEDED)
        self.assertEqual(job.result["sent"], 1)
        self.assertTrue(notification.is_emailed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Jobs processed: 1", out.getvalue())

    @patch("jobs.registry.send_pending_notification_emails_job", side_effect=RuntimeError("boom"))
    def test_failed_job_is_requeued_until_attempts_are_exhausted(self, _handler):
        with patch.dict("jobs.registry.JOB_HANDLERS", {"notifications.send_pending_emails": _handler}):
            job = BackgroundJob.enqueue("notifications.send_pending_emails", {"limit": 10}, max_attempts=2)
            claimed = BackgroundJob.claim_next(worker_id="test-worker")

            with self.assertRaises(RuntimeError):
                claimed.execute()

            job.refresh_from_db()
            self.assertEqual(job.status, BackgroundJob.STATUS_QUEUED)
            self.assertEqual(job.attempts, 1)
            self.assertIn("boom", job.last_error)

    def test_enqueue_periodic_jobs_adds_notification_email_job_once(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type="new_message",
            title="Mesaj nou",
            message="Ai primit un mesaj.",
        )

        call_command("enqueue_periodic_jobs", stdout=StringIO())
        call_command("enqueue_periodic_jobs", stdout=StringIO())

        self.assertEqual(
            BackgroundJob.objects.filter(name="notifications.send_pending_emails").count(),
            1,
        )
