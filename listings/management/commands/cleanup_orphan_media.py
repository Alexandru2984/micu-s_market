from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand
from django.db.models import FileField


class Command(BaseCommand):
    help = "Listează sau șterge fișierele din MEDIA_ROOT care nu mai sunt referențiate de modele."

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Șterge fișierele orfane găsite.")

    def handle(self, *args, **options):
        storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        if not isinstance(storage, FileSystemStorage):
            self.stderr.write("cleanup_orphan_media rulează doar pe storage local.")
            return

        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stdout.write("MEDIA_ROOT nu există.")
            return

        referenced = self._referenced_files()
        existing = {
            path.relative_to(media_root).as_posix()
            for path in media_root.rglob("*")
            if path.is_file()
        }
        orphaned = sorted(existing - referenced)

        if not orphaned:
            self.stdout.write(self.style.SUCCESS("Nu există fișiere media orfane."))
            return

        for name in orphaned:
            self.stdout.write(name)

        if options["delete"]:
            for name in orphaned:
                (media_root / name).unlink(missing_ok=True)
            self.stdout.write(self.style.SUCCESS(f"Șterse {len(orphaned)} fișiere media orfane."))
        else:
            self.stdout.write(self.style.WARNING(f"{len(orphaned)} fișiere orfane găsite. Rulează cu --delete pentru ștergere."))

    def _referenced_files(self):
        referenced = set()
        for model in apps.get_models():
            file_fields = [
                field for field in model._meta.get_fields()
                if isinstance(field, FileField)
            ]
            if not file_fields:
                continue

            queryset = model.objects.all()
            for field in file_fields:
                for value in queryset.exclude(**{f"{field.name}": ""}).values_list(field.name, flat=True):
                    if value:
                        referenced.add(str(value))
        return referenced
