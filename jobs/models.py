import socket
import uuid
from datetime import timedelta

from django.db import models, transaction
from django.db.models import F
from django.utils import timezone


class BackgroundJob(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_QUEUED, "În coadă"),
        (STATUS_RUNNING, "Rulează"),
        (STATUS_SUCCEEDED, "Reușit"),
        (STATUS_FAILED, "Eșuat"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    priority = models.PositiveSmallIntegerField(default=100)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    run_after = models.DateTimeField(default=timezone.now)
    locked_by = models.CharField(max_length=120, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "run_after", "created_at"]
        indexes = [
            models.Index(fields=["status", "priority", "run_after"]),
            models.Index(fields=["name", "status"]),
            models.Index(fields=["locked_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @classmethod
    def enqueue(cls, name, payload=None, *, priority=100, max_attempts=3, run_after=None):
        return cls.objects.create(
            name=name,
            payload=payload or {},
            priority=priority,
            max_attempts=max_attempts,
            run_after=run_after or timezone.now(),
        )

    @classmethod
    def recover_stale(cls, older_than_minutes=30):
        cutoff = timezone.now() - timedelta(minutes=older_than_minutes)
        return cls.objects.filter(
            status=cls.STATUS_RUNNING,
            locked_at__lt=cutoff,
            attempts__lt=F("max_attempts"),
        ).update(
            status=cls.STATUS_QUEUED,
            locked_by="",
            locked_at=None,
            last_error="Recovered stale running job.",
        )

    @classmethod
    def claim_next(cls, worker_id=None):
        worker = worker_id or f"{socket.gethostname()}:{uuid.uuid4()}"
        now = timezone.now()
        with transaction.atomic():
            job = (
                cls.objects.select_for_update(skip_locked=True)
                .filter(status=cls.STATUS_QUEUED, run_after__lte=now, attempts__lt=F("max_attempts"))
                .order_by("priority", "run_after", "created_at")
                .first()
            )
            if not job:
                return None

            job.status = cls.STATUS_RUNNING
            job.locked_by = worker
            job.locked_at = now
            job.started_at = now
            job.finished_at = None
            job.attempts += 1
            job.save(update_fields=["status", "locked_by", "locked_at", "started_at", "finished_at", "attempts", "updated_at"])
            return job

    def execute(self):
        from .registry import get_job_handler

        handler = get_job_handler(self.name)
        try:
            result = handler(self.payload)
        except Exception as exc:
            self.mark_failed(exc)
            raise
        else:
            self.mark_succeeded(result)
            return result

    def mark_succeeded(self, result=None):
        self.status = self.STATUS_SUCCEEDED
        self.result = result or {}
        self.last_error = ""
        self.finished_at = timezone.now()
        self.locked_by = ""
        self.locked_at = None
        self.save(update_fields=["status", "result", "last_error", "finished_at", "locked_by", "locked_at", "updated_at"])

    def mark_failed(self, exc):
        self.last_error = str(exc)
        self.locked_by = ""
        self.locked_at = None
        if self.attempts >= self.max_attempts:
            self.status = self.STATUS_FAILED
            self.finished_at = timezone.now()
        else:
            self.status = self.STATUS_QUEUED
            self.run_after = timezone.now() + timedelta(minutes=min(self.attempts * 5, 60))
        self.save(update_fields=["status", "run_after", "last_error", "finished_at", "locked_by", "locked_at", "updated_at"])
