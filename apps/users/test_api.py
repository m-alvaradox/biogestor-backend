from django.urls import reverse
from rest_framework.test import APITestCase

from .models import User


class UserListEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse("user-list")

    def test_returns_empty_list_when_there_are_no_users(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_returns_user_fields(self):
        user = User.objects.create(
            name="Dra. Ana Lima",
            email="ana@example.com",
            dept="Acuicultura",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": user.id,
                    "name": "Dra. Ana Lima",
                    "email": "ana@example.com",
                    "role": User.UserRole.ADMINISTRATOR,
                    "dept": "Acuicultura",
                    "status": User.UserStatus.ACTIVE,
                }
            ],
        )

    def test_excludes_inactive_users(self):
        active = User.objects.create(name="Ana Lima", email="ana@example.com")
        User.objects.create(
            name="Carlos Mora",
            email="carlos@example.com",
            status=User.UserStatus.INACTIVE,
        )

        response = self.client.get(self.url)

        self.assertEqual([item["id"] for item in response.json()], [active.id])

    def test_orders_by_name(self):
        for name, email in [
            ("Marta Ruiz", "marta@example.com"),
            ("Ana Lima", "ana@example.com"),
            ("Luis Vera", "luis@example.com"),
        ]:
            User.objects.create(name=name, email=email)

        response = self.client.get(self.url)

        self.assertEqual(
            [item["name"] for item in response.json()],
            ["Ana Lima", "Luis Vera", "Marta Ruiz"],
        )

    def test_rejects_write_methods(self):
        user = User.objects.create(name="Ana Lima", email="ana@example.com")

        for method in ["post", "put", "patch", "delete"]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, {"name": "Otro"})

                self.assertEqual(response.status_code, 405)
        self.assertEqual(list(User.objects.values_list("name", flat=True)), ["Ana Lima"])
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
