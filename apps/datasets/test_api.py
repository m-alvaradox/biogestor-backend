from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Dataset


class DatasetListEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse("dataset-list")

    def create_dataset(self, name, **fields):
        fields.setdefault("type", Dataset.DatasetType.AUDIO)
        return Dataset.objects.create(name=name, **fields)

    def names(self, response):
        return [item["name"] for item in response.json()["results"]]

    def test_returns_empty_page_when_there_are_no_datasets(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"count": 0, "next": None, "previous": None, "results": []},
        )

    def test_returns_list_fields_with_owner_id_or_null(self):
        owner = User.objects.create(name="Ana Pérez", email="ana@example.com")
        with_owner = self.create_dataset("Cantos de aves", owner=owner)
        without_owner = self.create_dataset(
            "Fotos de estanques",
            type=Dataset.DatasetType.IMAGE,
            status=Dataset.Status.PROCESSING,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = {item["id"]: item for item in response.json()["results"]}
        self.assertEqual(
            set(results[with_owner.id]),
            {"id", "name", "type", "status", "owner", "created_at"},
        )
        self.assertEqual(results[with_owner.id]["owner"], owner.id)
        self.assertIsNone(results[without_owner.id]["owner"])
        self.assertEqual(results[without_owner.id]["type"], "image")
        self.assertEqual(results[without_owner.id]["status"], "processing")

    def test_orders_by_newest_first_by_default(self):
        older = self.create_dataset("Antiguo")
        newer = self.create_dataset("Reciente")
        Dataset.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=1))

        response = self.client.get(self.url)

        self.assertEqual(self.names(response), [newer.name, older.name])

    def test_orders_by_requested_field(self):
        for name in ["Bravo", "Alfa", "Charlie"]:
            self.create_dataset(name)

        ascending = self.client.get(self.url, {"ordering": "name"})
        descending = self.client.get(self.url, {"ordering": "-name"})

        self.assertEqual(self.names(ascending), ["Alfa", "Bravo", "Charlie"])
        self.assertEqual(self.names(descending), ["Charlie", "Bravo", "Alfa"])

    def test_paginates_ten_results_by_default(self):
        for index in range(12):
            self.create_dataset(f"Dataset {index}")

        response = self.client.get(self.url)
        body = response.json()

        self.assertEqual(body["count"], 12)
        self.assertEqual(len(body["results"]), 10)
        self.assertIsNotNone(body["next"])
        self.assertIsNone(body["previous"])

    def test_accepts_page_and_page_size(self):
        for index in range(5):
            self.create_dataset(f"Dataset {index}")

        response = self.client.get(self.url, {"page": 2, "page_size": 2})
        body = response.json()

        self.assertEqual(len(body["results"]), 2)
        self.assertIsNotNone(body["next"])
        self.assertIsNotNone(body["previous"])

    def test_limits_page_size_to_one_hundred(self):
        Dataset.objects.bulk_create(
            Dataset(name=f"Dataset {index}", type=Dataset.DatasetType.CSV) for index in range(101)
        )

        response = self.client.get(self.url, {"page_size": 500})

        self.assertEqual(len(response.json()["results"]), 100)

    def test_returns_404_for_a_page_that_does_not_exist(self):
        self.create_dataset("Único")

        response = self.client.get(self.url, {"page": 5})

        self.assertEqual(response.status_code, 404)

    def test_searches_name_description_and_species(self):
        self.create_dataset("Camarón juvenil")
        self.create_dataset("Audio nocturno", description="Grabación de camarones")
        self.create_dataset("Muestras", species="Camarón blanco")
        self.create_dataset("Tilapia")

        response = self.client.get(self.url, {"search": "camar"})

        self.assertEqual(response.json()["count"], 3)
        self.assertNotIn("Tilapia", self.names(response))

    def test_filters_by_type_status_and_owner(self):
        owner = User.objects.create(name="Luis Mora", email="luis@example.com")
        self.create_dataset("Imagen activa", type=Dataset.DatasetType.IMAGE, owner=owner)
        self.create_dataset(
            "Imagen archivada",
            type=Dataset.DatasetType.IMAGE,
            status=Dataset.Status.ARCHIVED,
        )
        self.create_dataset("Audio activo")

        by_type = self.client.get(self.url, {"type": "image"})
        by_status = self.client.get(self.url, {"status": "archived"})
        by_owner = self.client.get(self.url, {"owner": owner.id})

        self.assertEqual(sorted(self.names(by_type)), ["Imagen activa", "Imagen archivada"])
        self.assertEqual(self.names(by_status), ["Imagen archivada"])
        self.assertEqual(self.names(by_owner), ["Imagen activa"])

    def test_rejects_invalid_filter_values(self):
        for params in [{"type": "pdf"}, {"status": "deleted"}, {"owner": "abc"}]:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)

                self.assertEqual(response.status_code, 400)
                self.assertIn(next(iter(params)), response.json())

    def test_is_available_without_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_rejects_post(self):
        response = self.client.post(self.url, {"name": "Nuevo", "type": "audio"})

        self.assertEqual(response.status_code, 405)
