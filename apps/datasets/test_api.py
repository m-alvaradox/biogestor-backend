from datetime import date, timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Dataset


def create_dataset(name, **fields):
    fields.setdefault("type", Dataset.DatasetType.AUDIO)
    return Dataset.objects.create(name=name, **fields)


@override_settings(DEBUG=True)
class DatasetListEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse("dataset-list")

    def names(self, response):
        return [item["name"] for item in response.json()["results"]]

    def test_returns_empty_page_when_there_are_no_datasets(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"count": 0, "next": None, "previous": None, "results": []},
        )

    def test_returns_list_fields_with_owner_summary_or_null(self):
        owner = User.objects.create(name="Ana Pérez", email="ana@example.com")
        with_owner = create_dataset("Cantos de aves", owner=owner)
        without_owner = create_dataset(
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
        self.assertEqual(results[with_owner.id]["owner"], {"id": owner.id, "name": "Ana Pérez"})
        self.assertIsNone(results[without_owner.id]["owner"])
        self.assertEqual(results[without_owner.id]["type"], "image")
        self.assertEqual(results[without_owner.id]["status"], "processing")

    def test_orders_by_newest_first_by_default(self):
        older = create_dataset("Antiguo")
        newer = create_dataset("Reciente")
        Dataset.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=1))

        response = self.client.get(self.url)

        self.assertEqual(self.names(response), [newer.name, older.name])

    def test_orders_by_requested_field(self):
        for name in ["Bravo", "Alfa", "Charlie"]:
            create_dataset(name)

        ascending = self.client.get(self.url, {"ordering": "name"})
        descending = self.client.get(self.url, {"ordering": "-name"})

        self.assertEqual(self.names(ascending), ["Alfa", "Bravo", "Charlie"])
        self.assertEqual(self.names(descending), ["Charlie", "Bravo", "Alfa"])

    def test_paginates_ten_results_by_default(self):
        for index in range(12):
            create_dataset(f"Dataset {index}")

        response = self.client.get(self.url)
        body = response.json()

        self.assertEqual(body["count"], 12)
        self.assertEqual(len(body["results"]), 10)
        self.assertIsNotNone(body["next"])
        self.assertIsNone(body["previous"])

    def test_accepts_page_and_page_size(self):
        for index in range(5):
            create_dataset(f"Dataset {index}")

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
        create_dataset("Único")

        response = self.client.get(self.url, {"page": 5})

        self.assertEqual(response.status_code, 404)

    def test_searches_name_description_and_species(self):
        create_dataset("Camarón juvenil")
        create_dataset("Audio nocturno", description="Grabación de camarones")
        create_dataset("Muestras", species="Camarón blanco")
        create_dataset("Tilapia")

        response = self.client.get(self.url, {"search": "camar"})

        self.assertEqual(response.json()["count"], 3)
        self.assertNotIn("Tilapia", self.names(response))

    def test_filters_by_type_status_and_owner(self):
        owner = User.objects.create(name="Luis Mora", email="luis@example.com")
        create_dataset("Imagen activa", type=Dataset.DatasetType.IMAGE, owner=owner)
        create_dataset(
            "Imagen archivada",
            type=Dataset.DatasetType.IMAGE,
            status=Dataset.Status.ARCHIVED,
        )
        create_dataset("Audio activo")

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

    def test_creates_dataset_with_required_fields(self):
        payload = {
            "name": "Nuevo dataset",
            "type": "audio",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201, response.content.decode())

        body = response.json()
        dataset = Dataset.objects.get(pk=body["id"])

        self.assertEqual(body["name"], "Nuevo dataset")
        self.assertEqual(body["type"], "audio")
        self.assertEqual(body["status"], "active")
        self.assertEqual(dataset.name, "Nuevo dataset")

    def test_creates_dataset_with_metadata_and_storage(self):
        payload = {
            "name": "Grabaciones de camarón",
            "type": "audio",
            "species": "Penaeus vannamei",
            "type_metadata": {"sample_rate": 44100},
            "storage": {
                "s3_uri": "s3://biogestor-data/audio/batch-001/",
                "file_format": ".WAV",
                "size_bytes": 4700000,
                "file_count": 25,
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201, response.content.decode())

        dataset = Dataset.objects.get(pk=response.json()["id"])
        self.assertEqual(dataset.species, "Penaeus vannamei")
        self.assertEqual(dataset.type_metadata["sample_rate"], 44100)
        self.assertEqual(
            dataset.s3_uri,
            "s3://biogestor-data/audio/batch-001/",
        )
        self.assertEqual(dataset.file_count, 25)

    def test_rejects_missing_required_fields(self):
        payloads = [
            ({"name": "Sin tipo"}, "type"),
            ({"type": "audio"}, "name"),
        ]

        for payload, field in payloads:
            with self.subTest(field=field):
                response = self.client.post(self.url, payload, format="json")

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

    def test_rejects_invalid_dataset_type(self):
        response = self.client.post(
            self.url,
            {"name": "Dataset inválido", "type": "pdf"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("type", response.json())

    def test_rejects_future_capture_date(self):
        future_date = (timezone.localdate() + timedelta(days=1)).isoformat()

        response = self.client.post(
            self.url,
            {
                "name": "Dataset futuro",
                "type": "audio",
                "capture_date": future_date,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Dataset.objects.count(), 0)

    def test_rejects_duplicate_s3_uri(self):
        s3_uri = "s3://biogestor-data/audio/duplicate/"
        Dataset.objects.create(
            name="Dataset existente",
            type="audio",
            s3_uri=s3_uri,
        )

        response = self.client.post(
            self.url,
            {
                "name": "Dataset duplicado",
                "type": "audio",
                "storage": {"s3_uri": s3_uri},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Dataset.objects.count(), 1)

    def test_post_is_hidden_when_debug_is_disabled(self):
        with override_settings(DEBUG=False):
            response = self.client.post(
                self.url,
                {"name": "No permitido", "type": "audio"},
                format="json",
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Dataset.objects.count(), 0)


class DatasetDetailEndpointTests(APITestCase):
    def url(self, pk):
        return reverse("dataset-detail", args=[pk])

    def test_returns_each_requested_dataset(self):
        owner = User.objects.create(name="Ana Lima", email="ana@example.com")
        audio = create_dataset(
            "Lote de audio de tilapia 001",
            owner=owner,
            species="Tilapia (Oreochromis niloticus)",
            farm="Aquamar Norte",
            pool="Piscina A-3",
            capture_date=date(2024, 10, 12),
            type_metadata={"microphone": "Hidrófono DolphinEar DE200", "sample_rate": 44100},
            s3_uri="s3://biogestor-data/tilapia/audio/batch-001/",
            file_format=".WAV",
            size_bytes=4_700_000_000,
            file_count=1247,
        )
        image = create_dataset(
            "Fotos de estanques",
            type=Dataset.DatasetType.IMAGE,
            status=Dataset.Status.ARCHIVED,
            species="Penaeus vannamei",
        )

        audio_body = self.client.get(self.url(audio.pk)).json()
        image_body = self.client.get(self.url(image.pk)).json()

        self.assertEqual(audio_body["id"], audio.pk)
        self.assertEqual(audio_body["name"], "Lote de audio de tilapia 001")
        self.assertEqual(audio_body["owner"], {"id": owner.id, "name": "Ana Lima"})
        self.assertEqual(audio_body["capture_date"], "2024-10-12")
        self.assertEqual(audio_body["type_metadata"]["sample_rate"], 44100)
        self.assertEqual(
            audio_body["storage"],
            {
                "s3_uri": "s3://biogestor-data/tilapia/audio/batch-001/",
                "file_format": ".WAV",
                "size_bytes": 4_700_000_000,
                "file_count": 1247,
            },
        )
        self.assertEqual(image_body["id"], image.pk)
        self.assertEqual(image_body["type"], "image")
        self.assertEqual(image_body["status"], "archived")
        self.assertEqual(image_body["species"], "Penaeus vannamei")

    def test_returns_only_prototype_fields(self):
        dataset = create_dataset("Cantos de aves")

        response = self.client.get(self.url(dataset.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()),
            {
                "id",
                "name",
                "type",
                "status",
                "owner",
                "created_at",
                "species",
                "farm",
                "pool",
                "capture_date",
                "type_metadata",
                "storage",
            },
        )

    def test_includes_every_list_field(self):
        dataset = create_dataset("Cantos de aves")

        list_item = self.client.get(reverse("dataset-list")).json()["results"][0]
        detail = self.client.get(self.url(dataset.pk)).json()

        self.assertLessEqual(set(list_item), set(detail))
        for field in list_item:
            with self.subTest(field=field):
                self.assertEqual(detail[field], list_item[field])

    def test_returns_null_for_empty_optional_fields(self):
        dataset = create_dataset("Solo obligatorios", status=None)

        body = self.client.get(self.url(dataset.pk)).json()

        for field in [
            "status",
            "owner",
            "species",
            "farm",
            "pool",
            "capture_date",
            "type_metadata",
        ]:
            with self.subTest(field=field):
                self.assertIsNone(body[field])
        self.assertEqual(
            body["storage"],
            {"s3_uri": None, "file_format": None, "size_bytes": None, "file_count": None},
        )

    def test_returns_404_for_a_dataset_that_does_not_exist(self):
        response = self.client.get(self.url(999999))

        self.assertEqual(response.status_code, 404)

    def test_is_available_without_authentication(self):
        dataset = create_dataset("Cantos de aves")

        response = self.client.get(self.url(dataset.pk))

        self.assertEqual(response.status_code, 200)

    def test_rejects_write_methods(self):
        dataset = create_dataset("Cantos de aves")

        for method in ["post", "put", "patch", "delete"]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url(dataset.pk), {})

                self.assertEqual(response.status_code, 405)
        self.assertTrue(Dataset.objects.filter(pk=dataset.pk).exists())
