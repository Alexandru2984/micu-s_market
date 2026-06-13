import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Verifică serviciile critice folosite de aplicație: DB, cache, email și storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-email",
            action="store_true",
            help="Nu deschide conexiunea către backend-ul de email.",
        )
        parser.add_argument(
            "--skip-storage",
            action="store_true",
            help="Nu face testul de scriere/citire/ștergere în storage.",
        )
        parser.add_argument(
            "--send-test-email",
            metavar="ADDRESS",
            help="Trimite un email de test către adresa dată după verificarea conexiunii.",
        )

    def handle(self, *args, **options):
        checks = [
            ("database", self._check_database),
            ("cache", self._check_cache),
        ]

        if not options["skip_email"]:
            checks.append(("email", lambda: self._check_email(options["send_test_email"])))

        if not options["skip_storage"]:
            checks.append(("storage", self._check_storage))

        failures = []
        for label, check in checks:
            try:
                detail = check()
            except Exception as exc:  # noqa: BLE001 - management command should report all external failures.
                failures.append((label, exc))
                self.stderr.write(self.style.ERROR(f"FAIL {label}: {exc}"))
            else:
                suffix = f" - {detail}" if detail else ""
                self.stdout.write(self.style.SUCCESS(f"OK {label}{suffix}"))

        if failures:
            failed_labels = ", ".join(label for label, _ in failures)
            raise CommandError(f"Doctor checks failed: {failed_labels}")

        self.stdout.write(self.style.SUCCESS("Doctor checks passed."))

    def _check_database(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        if result != (1,):
            raise RuntimeError("database returned an unexpected response")
        return connection.vendor

    def _check_cache(self):
        key = f"micu:doctor:{uuid.uuid4()}"
        expected = "ok"
        cache.set(key, expected, timeout=30)
        actual = cache.get(key)
        cache.delete(key)
        if actual != expected:
            raise RuntimeError("cache set/get returned an unexpected response")
        return getattr(settings, "RATELIMIT_USE_CACHE", "default")

    def _check_email(self, test_address):
        connection_obj = get_connection()
        connection_obj.open()
        connection_obj.close()

        if test_address:
            sent = send_mail(
                "Micu Market doctor test",
                "Email delivery check from manage.py doctor.",
                settings.DEFAULT_FROM_EMAIL,
                [test_address],
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError("test email was not accepted by the backend")
            return f"sent test email to {test_address}"

        return settings.EMAIL_BACKEND

    def _check_storage(self):
        name = f".doctor/{uuid.uuid4()}.txt"
        saved_name = default_storage.save(name, ContentFile(b"ok"))
        try:
            with default_storage.open(saved_name, "rb") as saved_file:
                content = saved_file.read()
            if content != b"ok":
                raise RuntimeError("storage read returned unexpected content")
        finally:
            default_storage.delete(saved_name)
        return default_storage.__class__.__name__
