from django.core.management.base import BaseCommand

from notifications.email import send_notification_email
from notifications.models import Notification


class Command(BaseCommand):
    help = "Trimite pe email notificările care nu au fost încă expediate."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Numărul maxim de notificări procesate.")

    def handle(self, *args, **options):
        notifications = (
            Notification.objects.filter(is_emailed=False)
            .select_related("recipient", "recipient__notification_preferences")
            .order_by("created_at")[: options["limit"]]
        )

        sent = 0
        for notification in notifications:
            if send_notification_email(notification):
                sent += 1

        self.stdout.write(self.style.SUCCESS(f"Emailuri notificări trimise: {sent}"))
