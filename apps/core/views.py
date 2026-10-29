"""Endpoints transversales del backend."""

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import IntegrationProbe


@require_GET
def health(_request):
    """Confirma que el proceso HTTP de BioGestor está respondiendo."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "biogestor-backend",
        }
    )


@require_GET
def health_database(_request):
    """Confirma que el backend puede consultar PostgreSQL"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)

    return JsonResponse({"status": "ok", "database": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def integration(_request):
    if not settings.DEBUG:
        return Response({"detail": "No encontrado."}, status=404)

    probe = IntegrationProbe.objects.filter(pk="sprint-0").first()

    if probe is None:
        return Response({"detail": "Registro de prueba no encontrado."}, status=404)

    return Response(
        {
            "id": probe.id,
            "message": probe.message,
        }
    )
