"""Tests for the datasets module."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.users.models import User

from ..models import Dataset


class DatasetRequiredFieldsTests(TestCase):
    """name and type are required.

    Django does not call full_clean() on save(), so these rules are checked
    explicitly the same way a form or serializer would do it.
    """

    def test_valid_with_only_name_and_type(self):
        dataset = Dataset(name="Audio pool A-3", type=Dataset.DatasetType.AUDIO)

        dataset.full_clean()
        dataset.save()

        saved = Dataset.objects.get(pk=dataset.pk)
        self.assertEqual(saved.name, "Audio pool A-3")
        self.assertEqual(saved.type, Dataset.DatasetType.AUDIO)
        self.assertEqual(saved.status, Dataset.Status.ACTIVE)
        self.assertEqual(str(saved), "Audio pool A-3 (Audio)")

    def test_name_is_required(self):
        dataset = Dataset(name="", type=Dataset.DatasetType.AUDIO)

        with self.assertRaises(ValidationError) as error:
            dataset.full_clean()

        self.assertIn("name", error.exception.message_dict)

    def test_type_is_required(self):
        dataset = Dataset(name="Dataset without type")

        with self.assertRaises(ValidationError) as error:
            dataset.full_clean()

        self.assertIn("type", error.exception.message_dict)

    def test_type_must_be_a_valid_choice(self):
        dataset = Dataset(name="Wrong type", type="pdf")

        with self.assertRaises(ValidationError) as error:
            dataset.full_clean()

        self.assertIn("type", error.exception.message_dict)


class DatasetCaptureDateTests(TestCase):
    def test_capture_date_is_optional(self):
        dataset = Dataset(name="No date", type=Dataset.DatasetType.CSV)

        dataset.full_clean()
        dataset.save()

        self.assertIsNone(Dataset.objects.get(pk=dataset.pk).capture_date)

    def test_accepts_past_or_today_capture_date(self):
        dataset = Dataset(
            name="Today", type=Dataset.DatasetType.IMAGE, capture_date=timezone.localdate()
        )

        dataset.full_clean()
        dataset.save()

        self.assertEqual(Dataset.objects.count(), 1)

    def test_full_clean_rejects_future_capture_date(self):
        future = timezone.localdate() + timedelta(days=2)
        dataset = Dataset(name="Future", type=Dataset.DatasetType.AUDIO, capture_date=future)

        with self.assertRaises(ValidationError) as error:
            dataset.full_clean()

        self.assertIn("La fecha de captura no puede ser futura.", error.exception.messages)

    def test_database_rejects_future_capture_date(self):
        future = timezone.localdate() + timedelta(days=2)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Dataset.objects.create(
                name="Future", type=Dataset.DatasetType.AUDIO, capture_date=future
            )


class DatasetPersistenceTests(TestCase):
    def test_saves_and_reads_metadata(self):
        created = Dataset.objects.create(
            name="Weight sampling images",
            type=Dataset.DatasetType.IMAGE,
            species="Penaeus vannamei",
            farm="Demo farm",
            pool="B-1",
            s3_uri="s3://biogestor-demo/images/b-1/",
            type_metadata={"resolution": "1920x1080"},
        )

        dataset = Dataset.objects.get(pk=created.pk)
        self.assertEqual(dataset.farm, "Demo farm")
        self.assertEqual(dataset.type_metadata["resolution"], "1920x1080")

    def test_same_s3_uri_cannot_be_registered_twice(self):
        Dataset.objects.create(name="A", type="audio", s3_uri="s3://biogestor-demo/a/")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Dataset.objects.create(name="Copy", type="audio", s3_uri="s3://biogestor-demo/a/")

    def test_several_datasets_without_s3_uri_are_allowed(self):
        Dataset.objects.create(name="A", type="other")
        Dataset.objects.create(name="B", type="other")

        self.assertEqual(Dataset.objects.filter(s3_uri__isnull=True).count(), 2)

    def test_owner_is_a_user_and_cannot_be_deleted_while_owning_datasets(self):
        owner = User.objects.create(name="Ana Lima", email="ana@example.com")
        dataset = Dataset.objects.create(name="A", type="audio", owner=owner)

        self.assertEqual(owner.datasets.get(), dataset)
        with self.assertRaises(ProtectedError):
            owner.delete()

    def test_optional_fields_are_stored_as_null(self):
        dataset = Dataset.objects.create(name="Only required", type=Dataset.DatasetType.TEXT)

        saved = Dataset.objects.get(pk=dataset.pk)
        optional_fields = [
            "owner",
            "description",
            "species",
            "farm",
            "pool",
            "capture_date",
            "license",
            "type_metadata",
            "s3_uri",
            "file_format",
            "size_bytes",
            "file_count",
        ]
        for field in optional_fields:
            with self.subTest(field=field):
                self.assertIsNone(getattr(saved, field))

    def test_status_accepts_null(self):
        dataset = Dataset.objects.create(name="No status", type="csv", status=None)

        self.assertIsNone(Dataset.objects.get(pk=dataset.pk).status)
