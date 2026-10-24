"""Dataset catalog."""

from django.db import models
from django.db.models.functions import Now


class Dataset(models.Model):
    """Dataset registered in BioGestor.

    BioGestor does not upload or copy files: it only stores the reference to an
    object or folder that already exists in S3, together with its metadata.
    """

    class DatasetType(models.TextChoices):
        AUDIO = "audio", "Audio"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        CSV = "csv", "CSV"
        TEXT = "text", "Text"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PROCESSING = "processing", "Processing"
        ARCHIVED = "archived", "Archived"
        ERROR = "error", "Error"

    # Required metadata (PO decision)
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=20, choices=DatasetType.choices)

    # Prototype list view: name, type, researcher (owner), registration date, status
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="datasets",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Prototype detail view: metadata
    description = models.TextField(blank=True)
    species = models.CharField(max_length=100, blank=True)
    farm = models.CharField(max_length=100, blank=True)
    pool = models.CharField(max_length=50, blank=True)
    capture_date = models.DateField(null=True, blank=True)
    license = models.CharField(max_length=100, blank=True)
    # Fields that depend on the type (microphone, sample rate, resolution...)
    type_metadata = models.JSONField(default=dict, blank=True)

    # Prototype detail view: storage
    s3_uri = models.CharField(max_length=1024, blank=True)
    file_format = models.CharField(max_length=30, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    file_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["s3_uri"],
                condition=~models.Q(s3_uri=""),
                name="dataset_unique_s3_uri",
                violation_error_message="Ya existe un dataset con esta referencia de S3.",
            ),
            models.CheckConstraint(
                condition=models.Q(capture_date__isnull=True) | models.Q(capture_date__lte=Now()),
                name="dataset_capture_date_not_in_future",
                violation_error_message="La fecha de captura no puede ser futura.",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
