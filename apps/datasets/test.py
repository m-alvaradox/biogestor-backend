from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Dataset


class DatasetPersistenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")

    def test_persiste_con_metadatos(self):
        ds = Dataset.objects.create(
            name="Audio piscina 3",
            type=Dataset.Type.AUDIO,
            owner=self.user,
            storage_uri="s3://biogestor-datasets/audio/p3-001.wav",
            farm="Camaronera Norte",
            pond="P3",
            metadata={"microfono": "hidrofono-A", "ruido_db": 42},
            tags=["piloto"],
        )
        ds.refresh_from_db()
        self.assertEqual(ds.metadata["microfono"], "hidrofono-A")
        self.assertEqual(ds.status, Dataset.Status.ACTIVE)

    def test_nombre_y_tipo_obligatorios(self):
        with self.assertRaises(ValidationError) as ctx:
            Dataset(name="", type="").full_clean()
        self.assertIn("name", ctx.exception.message_dict)
        self.assertIn("type", ctx.exception.message_dict)

    def test_rechaza_uri_que_no_es_s3(self):
        with self.assertRaises(ValidationError):
            Dataset(name="X", type="audio", storage_uri="https://ejemplo.com/a.wav").full_clean()

    def test_no_duplica_referencia_s3(self):
        uri = "s3://biogestor-datasets/audio/p3-001.wav"
        Dataset.objects.create(name="A", type="audio", storage_uri=uri)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dataset.objects.create(name="B", type="audio", storage_uri=uri)

    def test_varios_datasets_sin_referencia_son_validos(self):
        Dataset.objects.create(name="A", type="csv")
        Dataset.objects.create(name="B", type="csv")
        self.assertEqual(Dataset.objects.count(), 2)
