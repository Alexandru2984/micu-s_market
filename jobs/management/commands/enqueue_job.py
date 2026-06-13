import json

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from jobs.models import BackgroundJob
from jobs.registry import get_job_handler


class Command(BaseCommand):
    help = "Adaugă un job în coada de fundal."

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("--payload", default="{}", help="Payload JSON pentru handler.")
        parser.add_argument("--priority", type=int, default=100)
        parser.add_argument("--max-attempts", type=int, default=3)
        parser.add_argument("--run-after", help="Dată ISO la care jobul devine eligibil.")

    def handle(self, *args, **options):
        name = options["name"]
        try:
            get_job_handler(name)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        try:
            payload = json.loads(options["payload"])
        except json.JSONDecodeError as exc:
            raise CommandError(f"Payload invalid: {exc}") from exc
        if not isinstance(payload, dict):
            raise CommandError("Payload trebuie să fie un obiect JSON.")

        run_after = None
        if options["run_after"]:
            run_after = parse_datetime(options["run_after"])
            if run_after is None:
                raise CommandError("--run-after trebuie să fie ISO datetime.")
            if timezone.is_naive(run_after):
                run_after = timezone.make_aware(run_after)

        job = BackgroundJob.enqueue(
            name,
            payload,
            priority=options["priority"],
            max_attempts=options["max_attempts"],
            run_after=run_after,
        )
        self.stdout.write(self.style.SUCCESS(f"Job queued: {job.id} {job.name}"))
