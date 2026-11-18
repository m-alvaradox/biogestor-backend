"""Creates or updates the login password of a platform user.

Usage:
    python manage.py set_user_password ana@example.com

The password is asked interactively (it is never passed as an argument, so it
does not end up in the shell history) and validated with AUTH_PASSWORD_VALIDATORS.
"""

import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.users.models import User


class Command(BaseCommand):
    help = "Crea o cambia la contraseña de inicio de sesión de un usuario de la plataforma."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Correo del usuario (users.User).")

    def handle(self, *args, email, **options):
        profile = User.objects.select_related("account").filter(email__iexact=email).first()
        if profile is None:
            raise CommandError(f"No existe un usuario con el correo {email}.")

        password = getpass.getpass("Contraseña: ")
        if password != getpass.getpass("Repite la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")

        account = profile.account or get_user_model()(username=f"user-{profile.pk}")
        account.email = profile.email
        try:
            validate_password(password, user=account)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error

        with transaction.atomic():
            account.set_password(password)
            account.save()
            if profile.account_id != account.pk:
                profile.account = account
                profile.save(update_fields=["account"])

        self.stdout.write(self.style.SUCCESS(f"Contraseña guardada para {profile.email}."))
