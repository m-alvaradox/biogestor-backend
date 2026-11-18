"""Platform users, as defined in the class diagram."""

from django.conf import settings
from django.db import models


class User(models.Model):
    """Person responsible for datasets and other assets.

    Credentials live in the linked Django account (``account``), so the
    password is hashed and checked by ``django.contrib.auth``. Permissions
    per role belong to another deliverable.
    """

    class UserRole(models.TextChoices):
        # Only the administrator role for now (PO decision).
        ADMINISTRATOR = "administrator", "Administrator"

    class UserStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=UserRole.choices, default=UserRole.ADMINISTRATOR)
    dept = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile",
        help_text="Django account that stores the password. Empty means the user cannot log in.",
    )

    class Meta:
        ordering = ["name"]

    @property
    def is_active(self):
        return self.status == self.UserStatus.ACTIVE

    def __str__(self):
        return f"{self.name} <{self.email}>"
