"""Matriz de permisos de BioGestor (Tabla 2 del reporte de fase 1).

Este archivo es el único lugar donde se decide qué rol puede hacer qué.
Las vistas solo dicen qué operación realizan.
"""

from django.db import models
from rest_framework.permissions import BasePermission

from .models import Rol


class Operacion(models.TextChoices):
    CONSULTAR_DATASETS = "consultar_datasets", "Consultar datasets"
    CONSULTAR_MODELOS = "consultar_modelos", "Consultar modelos y versiones"
    REGISTRAR_DATASETS = "registrar_datasets", "Registrar datasets"
    MODIFICAR_METADATOS = "modificar_metadatos", "Modificar metadatos"
    REGISTRAR_VERSIONES = "registrar_versiones", "Registrar versiones de modelos"
    COMPARAR_MODELOS = "comparar_modelos", "Comparar modelos"
    APROBAR_MODELOS = "aprobar_modelos", "Aprobar o rechazar modelos"
    CAMBIAR_ESTADO_MODELOS = "cambiar_estado_modelos", "Cambiar estado de modelos"
    EJECUTAR_PRUEBAS = "ejecutar_pruebas", "Ejecutar o solicitar pruebas"
    MONITOREAR_INTEGRACION = "monitorear_integracion", "Monitorear integración API"
    CONFIGURAR_ALMACENAMIENTO = "configurar_almacenamiento", "Configurar almacenamiento"
    GESTIONAR_USUARIOS = "gestionar_usuarios", "Gestionar usuarios y roles"
    CONSULTAR_AUDITORIA = "consultar_auditoria", "Consultar auditoría"
    REGISTRAR_OBSERVACIONES = "registrar_observaciones", "Registrar observaciones"
    # "Modificar auditoría" no existe a propósito: nadie puede hacerlo.


ADMIN = Rol.ADMINISTRADOR
PO = Rol.PRODUCT_OWNER
ING = Rol.INGENIERO_DATOS
MLOPS = Rol.ML_OPERATOR
CIENT = Rol.CIENTIFICO_DATOS
TODOS = frozenset(Rol)

MATRIZ = {
    Operacion.CONSULTAR_DATASETS: TODOS,
    Operacion.CONSULTAR_MODELOS: TODOS,
    Operacion.REGISTRAR_DATASETS: frozenset({ADMIN, ING}),
    Operacion.MODIFICAR_METADATOS: frozenset({ADMIN, ING}),
    Operacion.REGISTRAR_VERSIONES: frozenset({ADMIN, ING}),
    Operacion.COMPARAR_MODELOS: TODOS,
    Operacion.APROBAR_MODELOS: frozenset({ADMIN, PO}),
    # RF-12 solo nombra a PO y Administrador. La Tabla 2 da "Limitado" al
    # Ingeniero de Datos sin decir qué significa: pendiente de confirmar con el PO.
    Operacion.CAMBIAR_ESTADO_MODELOS: frozenset({ADMIN, PO}),
    Operacion.EJECUTAR_PRUEBAS: frozenset({ADMIN, PO, MLOPS}),
    Operacion.MONITOREAR_INTEGRACION: frozenset({ADMIN, ING}),
    Operacion.CONFIGURAR_ALMACENAMIENTO: frozenset({ADMIN, ING}),
    Operacion.GESTIONAR_USUARIOS: frozenset({ADMIN}),
    # PO ve una parte ("Limitado") e Ingeniero la parte técnica: el filtro de
    # qué registros ve cada uno se hará en la vista de auditoría.
    Operacion.CONSULTAR_AUDITORIA: frozenset({ADMIN, PO, ING}),
    # No está en la Tabla 2. RF-14 / HU-09 la piden para el Científico de Datos,
    # así que se permite a todos hasta que el PO diga otra cosa.
    Operacion.REGISTRAR_OBSERVACIONES: TODOS,
}


def tiene_permiso(usuario, operacion):
    """True si el usuario está autenticado, activo y su rol permite la operación."""
    if not usuario or not usuario.is_authenticated or not usuario.is_active:
        return False
    return usuario.rol in MATRIZ.get(operacion, frozenset())


def operaciones_de(usuario):
    """Lista de operaciones permitidas, para que el frontend muestre u oculte botones."""
    return sorted(op.value for op in Operacion if tiene_permiso(usuario, op))


def requiere(operacion):
    """Clase de permiso DRF para una vista que realiza siempre la misma operación.

    Uso: permission_classes = [requiere(Operacion.GESTIONAR_USUARIOS)]
    """

    class _Requiere(BasePermission):
        def has_permission(self, request, view):
            return tiene_permiso(request.user, operacion)

    _Requiere.__name__ = f"Requiere_{operacion}"
    return _Requiere


class PermisoPorMetodo(BasePermission):
    """Permiso para vistas que hacen operaciones distintas según el método HTTP.

    La vista declara, por ejemplo:
        operaciones = {
            "GET": Operacion.CONSULTAR_DATASETS,
            "POST": Operacion.REGISTRAR_DATASETS,
            "PATCH": Operacion.MODIFICAR_METADATOS,
        }
    Un método que no está en el diccionario se rechaza.
    """

    def has_permission(self, request, view):
        metodo = "GET" if request.method in ("HEAD", "OPTIONS") else request.method
        operacion = getattr(view, "operaciones", {}).get(metodo)
        return operacion is not None and tiene_permiso(request.user, operacion)
