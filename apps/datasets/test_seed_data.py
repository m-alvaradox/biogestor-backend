"""Tests del comando seed_data."""

from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.users.models import User

from .management.commands.seed_data import DATASETS, USERS
from .models import Dataset


def run_seed(**options):
    call_command("seed_data", stdout=StringIO(), **options)


@override_settings(DEBUG=True)
class SeedDataTests(TestCase):
    def test_creates_users_and_datasets(self):
        run_seed()

        self.assertEqual(User.objects.count(), len(USERS))
        self.assertEqual(Dataset.objects.count(), len(DATASETS))

    def test_running_twice_does_not_duplicate(self):
        run_seed()
        run_seed()

        self.assertEqual(User.objects.count(), len(USERS))
        self.assertEqual(Dataset.objects.count(), len(DATASETS))

    def test_second_run_creates_nothing_in_any_seeded_app(self):
        """Idempotencia global: cubre también los modelos que se agreguen después."""
        seeded_models = [
            model
            for label in ("users", "datasets", "ml_models", "experiments", "observations")
            for model in apps.get_app_config(label).get_models()
        ]

        run_seed()
        first = {model: model.objects.count() for model in seeded_models}
        run_seed()
        second = {model: model.objects.count() for model in seeded_models}

        self.assertEqual(first, second)

    def test_dataset_owners_are_seeded_users(self):
        run_seed()

        with_owner = Dataset.objects.filter(owner__isnull=False)
        self.assertTrue(with_owner.exists())
        for dataset in with_owner:
            self.assertTrue(dataset.owner.email.endswith("@example.com"))

    def test_seeded_datasets_pass_validation(self):
        run_seed()

        for dataset in Dataset.objects.all():
            dataset.full_clean()

    def test_does_not_touch_existing_non_seed_records(self):
        User.objects.create(name="Real", email="real@example.org")

        run_seed()

        self.assertTrue(User.objects.filter(email="real@example.org").exists())


class SeedDataGuardTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuses_to_run_without_debug(self):
        with self.assertRaises(CommandError):
            run_seed()
        self.assertEqual(Dataset.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_force_overrides_the_guard(self):
        run_seed(force=True)

        self.assertEqual(Dataset.objects.count(), len(DATASETS))
