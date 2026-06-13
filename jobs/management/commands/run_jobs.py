import socket
import uuid

from django.core.management.base import BaseCommand

from jobs.models import BackgroundJob


class Command(BaseCommand):
    help = "Rulează joburi din coada de fundal."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--worker-id", default="")
        parser.add_argument("--recover-stale-minutes", type=int, default=30)

    def handle(self, *args, **options):
        worker_id = options["worker_id"] or f"{socket.gethostname()}:{uuid.uuid4()}"
        recovered = BackgroundJob.recover_stale(options["recover_stale_minutes"])
        if recovered:
            self.stdout.write(self.style.WARNING(f"Recovered stale jobs: {recovered}"))

        processed = 0
        for _ in range(options["limit"]):
            job = BackgroundJob.claim_next(worker_id=worker_id)
            if job is None:
                break
            try:
                result = job.execute()
            except Exception as exc:  # noqa: BLE001 - worker must continue with remaining jobs.
                self.stderr.write(self.style.ERROR(f"FAIL {job.id} {job.name}: {exc}"))
            else:
                processed += 1
                self.stdout.write(self.style.SUCCESS(f"OK {job.id} {job.name}: {result}"))

        self.stdout.write(self.style.SUCCESS(f"Jobs processed: {processed}"))
