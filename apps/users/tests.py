"""Tests for the users module."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import User


class UserModelTests(TestCase):
    def test_defaults_to_active_administrator(self):
        user = User(name="Ana Lima", email="ana@example.com")

        user.full_clean()
        user.save()

        saved = User.objects.get(pk=user.pk)
        self.assertEqual(saved.role, User.UserRole.ADMINISTRATOR)
        self.assertEqual(saved.status, User.UserStatus.ACTIVE)
        self.assertEqual(str(saved), "Ana Lima <ana@example.com>")

    def test_name_and_email_are_required(self):
        with self.assertRaises(ValidationError) as error:
            User(name="", email="").full_clean()

        self.assertIn("name", error.exception.message_dict)
        self.assertIn("email", error.exception.message_dict)

    def test_only_defined_roles_are_valid(self):
        user = User(name="Carlos", email="carlos@example.com", role="data_scientist")

        with self.assertRaises(ValidationError) as error:
            user.full_clean()

        self.assertIn("role", error.exception.message_dict)

    def test_email_is_unique(self):
        User.objects.create(name="A", email="same@example.com")

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(name="B", email="same@example.com")
