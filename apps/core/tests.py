"""Pruebas del módulo core."""

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import IntegrationProbe


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "status": "ok",
                "service": "biogestor-backend",
            },
        )

    def test_health_endpoint_rejects_post(self):
        response = self.client.post(reverse("health"))

        self.assertEqual(response.status_code, 405)


@override_settings(DEBUG=True)
class IntegrationEndpointTests(TestCase):
    def test_returns_record_from_database(self):
        IntegrationProbe.objects.create(
            id="sprint-0",
            message="Mensaje de prueba desde la BD",
        )

        response = self.client.get(reverse("integration"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": "sprint-0",
                "message": "Mensaje de prueba desde la BD",
            },
        )

    def test_returns_404_when_record_is_missing(self):
        response = self.client.get(reverse("integration"))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Registro de prueba no encontrado."},
        )

    def test_rejects_post(self):
        response = self.client.post(reverse("integration"))

        self.assertEqual(response.status_code, 405)

    @override_settings(DEBUG=False)
    def test_is_disabled_outside_development(self):
        IntegrationProbe.objects.create(
            id="sprint-0",
            message="Registro que no debe exponerse",
        )

        response = self.client.get(reverse("integration"))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "No encontrado."},
        )
