from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from favorites.models import SavedSearch
from jobs.models import BackgroundJob
from notifications.models import Notification

SAVED_SEARCH_ALERTS_INTERVAL_MINUTES = 15


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

        if self._should_queue_saved_search_alerts():
            BackgroundJob.enqueue("favorites.saved_search_alerts", priority=80)
            queued += 1
            self.stdout.write(self.style.SUCCESS("Queued favorites.saved_search_alerts"))

        self.stdout.write(self.style.SUCCESS(f"Periodic jobs queued: {queued}"))

    def _should_queue_saved_search_alerts(self):
        if not SavedSearch.objects.filter(is_active=True).exists():
            return False
        job_in_flight = BackgroundJob.objects.filter(
            name="favorites.saved_search_alerts",
            status__in=[BackgroundJob.STATUS_QUEUED, BackgroundJob.STATUS_RUNNING],
        ).exists()
        if job_in_flight:
            return False
        # The enqueue timer fires every minute; alerts only need to run
        # every SAVED_SEARCH_ALERTS_INTERVAL_MINUTES.
        recent_cutoff = timezone.now() - timedelta(minutes=SAVED_SEARCH_ALERTS_INTERVAL_MINUTES)
        return not BackgroundJob.objects.filter(
            name="favorites.saved_search_alerts",
            finished_at__gte=recent_cutoff,
        ).exists()
