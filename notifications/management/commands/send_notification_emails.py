from django.core.management.base import BaseCommand

from notifications.email import send_pending_notification_emails


class Command(BaseCommand):
    help = "Trimite pe email notificările care nu au fost încă expediate."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Numărul maxim de notificări procesate.")

    def handle(self, *args, **options):
        sent = send_pending_notification_emails(limit=options["limit"])

        self.stdout.write(self.style.SUCCESS(f"Emailuri notificări trimise: {sent}"))
