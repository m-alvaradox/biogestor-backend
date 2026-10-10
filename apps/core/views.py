"""Endpoints transversales del backend."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(_request):
    """Confirma que el proceso HTTP de BioGestor está respondiendo."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "biogestor-backend",
        }
    )
