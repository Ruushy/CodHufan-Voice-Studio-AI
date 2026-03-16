import uuid
from django.db import models
from django.utils import timezone


class ProcessingJob(models.Model):
    """Represents a single voice enhancement job."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=500)
    upload_path = models.CharField(max_length=1000)
    output_path = models.CharField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress_percent = models.IntegerField(default=0)
    current_stage = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)
    processing_log = models.JSONField(default=dict, blank=True)
    file_size_mb = models.FloatField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    elapsed_seconds = models.FloatField(null=True, blank=True)
    methods_used = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} — {self.original_filename} [{self.status}]"

    @property
    def output_filename(self):
        from pathlib import Path
        if self.output_path:
            return Path(self.output_path).name
        return ''

    @property
    def output_url(self):
        """Returns media URL for the processed file."""
        if not self.output_path:
            return None
        from pathlib import Path
        from django.conf import settings
        try:
            rel = Path(self.output_path).relative_to(settings.MEDIA_ROOT)
            return settings.MEDIA_URL + str(rel).replace('\\', '/')
        except ValueError:
            return None

    @property
    def upload_url(self):
        """Returns media URL for the original uploaded file."""
        if not self.upload_path:
            return None
        from pathlib import Path
        from django.conf import settings
        try:
            rel = Path(self.upload_path).relative_to(settings.MEDIA_ROOT)
            return settings.MEDIA_URL + str(rel).replace('\\', '/')
        except ValueError:
            return None

    @property
    def duration_formatted(self):
        if not self.duration_seconds:
            return 'Unknown'
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        return f"{mins}:{secs:02d}"
