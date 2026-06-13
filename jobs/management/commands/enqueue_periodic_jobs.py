from django.core.management.base import BaseCommand

from jobs.models import BackgroundJob
from notifications.models import Notification


class Command(BaseCommand):
    help = "Pune în coadă joburile periodice care au lucru de făcut."

    def handle(self, *args, **options):
        queued = 0
        pending_emails = Notification.objects.filter(is_emailed=False).exists()
        existing_email_job = BackgroundJob.objects.filter(
            name="notifications.send_pending_emails",
            status__in=[BackgroundJob.STATUS_QUEUED, BackgroundJob.STATUS_RUNNING],
        ).exists()

        if pending_emails and not existing_email_job:
            BackgroundJob.enqueue("notifications.send_pending_emails", {"limit": 200}, priority=50)
            queued += 1
            self.stdout.write(self.style.SUCCESS("Queued notifications.send_pending_emails"))

        self.stdout.write(self.style.SUCCESS(f"Periodic jobs queued: {queued}"))
