from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "departamento", "is_active")
    list_filter = ("rol", "departamento", "is_active")
    fieldsets = UserAdmin.fieldsets + (("BioGestor", {"fields": ("rol", "departamento")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("BioGestor", {"fields": ("email", "rol", "departamento")}),
    )
