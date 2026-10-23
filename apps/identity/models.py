"""Identidad y control de acceso."""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Rol(models.TextChoices):
    """Roles definidos en Ingeniería de Software I (Tabla 1 del reporte, acta AC-12)."""

    ADMINISTRADOR = "administrador", "Administrador"
    PRODUCT_OWNER = "product_owner", "Product Owner"
    INGENIERO_DATOS = "ingeniero_datos", "Ingeniero de Datos"
    ML_OPERATOR = "ml_operator", "Machine Learning Operator"
    CIENTIFICO_DATOS = "cientifico_datos", "Científico de Datos"


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Quien crea `createsuperuser` es el Administrador de la plataforma.
        extra_fields.setdefault("rol", Rol.ADMINISTRADOR)
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Persona con acceso a BioGestor.

    El rol se guarda aquí y no en el proveedor de login, para que el futuro
    inicio de sesión con cuentas de BioDynamics (AC-10) no cambie los permisos.
    El estado activo/inactivo es el campo `is_active` que ya trae Django.
    """

    email = models.EmailField("correo electrónico", unique=True)
    # Por defecto el rol con menos permisos (solo lectura).
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CIENTIFICO_DATOS)
    departamento = models.CharField(max_length=100, blank=True)

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
