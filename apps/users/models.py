"""Platform users, as defined in the class diagram."""

from django.db import models


class User(models.Model):
    """Person responsible for datasets and other assets.

    This is a domain model only: it does not handle authentication,
    passwords or permissions (those belong to another deliverable).
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

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
