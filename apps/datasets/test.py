from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Dataset


class DatasetPersistenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "ana", email="ana@biogestor.test", password="x"
        )

    def test_persiste_con_metadatos(self):
        ds = Dataset.objects.create(
            nombre="Audio piscina 3",
            tipo=Dataset.Tipo.AUDIO,
            propietario=self.user,
            ubicacion_s3="s3://biogestor-datasets/audio/p3-001.wav",
            granja="Camaronera Norte",
            piscina="P3",
            metadatos_tipo={"microfono": "hidrofono-A", "ruido_db": 42},
        )
        ds.refresh_from_db()
        self.assertEqual(ds.metadatos_tipo["microfono"], "hidrofono-A")
        self.assertEqual(ds.estado, Dataset.Estado.ACTIVO)
        self.assertEqual(ds.propietario, self.user)

    def test_nombre_y_tipo_obligatorios(self):
        with self.assertRaises(ValidationError) as ctx:
            Dataset(nombre="", tipo="").full_clean()
        self.assertIn("nombre", ctx.exception.message_dict)
        self.assertIn("tipo", ctx.exception.message_dict)

    def test_rechaza_uri_que_no_es_s3(self):
        with self.assertRaises(ValidationError):
            Dataset(nombre="X", tipo="audio", ubicacion_s3="https://ejemplo.com/a.wav").full_clean()

    def test_no_duplica_referencia_s3(self):
        uri = "s3://biogestor-datasets/audio/p3-001.wav"
        Dataset.objects.create(nombre="A", tipo="audio", ubicacion_s3=uri)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dataset.objects.create(nombre="B", tipo="audio", ubicacion_s3=uri)

    def test_varios_datasets_sin_referencia_son_validos(self):
        Dataset.objects.create(nombre="A", tipo="csv")
        Dataset.objects.create(nombre="B", tipo="csv")
        self.assertEqual(Dataset.objects.count(), 2)
