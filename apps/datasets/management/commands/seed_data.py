"""Carga datos semilla ficticios para desarrollo.

Uso:
    python manage.py seed_data

Es idempotente: cada registro se identifica por una clave natural y se crea con
get_or_create / update_or_create, así que ejecutarlo varias veces no duplica nada.

Todos los datos son ficticios (correos @example.com, bucket s3://biogestor-seed/).
No incluye contraseñas, tokens ni credenciales.
"""

import hashlib
from datetime import date, datetime, timezone

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.datasets.models import Dataset
from apps.users.models import User

# Nombres de clase esperados por entidad (app, [candidatos])

MODEL_CANDIDATES = {
    "dataset_version": ("datasets", ["DatasetVersion"]),
    "ml_model": ("ml_models", ["MLModel", "Model"]),
    "model_version": ("ml_models", ["ModelVersion"]),
    "model_version_dataset": (
        "ml_models",
        ["ModelVersionDatasetVersion", "ModelVersionDataset"],
    ),
    "experiment": ("experiments", ["Experiment"]),
    "observation": ("observations", ["Observation", "Comment"]),
}


def get_model_or_none(key):
    app_label, names = MODEL_CANDIDATES[key]
    for name in names:
        try:
            return apps.get_model(app_label, name)
        except LookupError:
            continue
    return None


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def fake_checksum(text):
    """Huella determinista y ficticia (no corresponde a ningún archivo real)."""
    return hashlib.sha256(text.encode()).hexdigest()


# Datos ficticios

ANA = "ana.lima@example.com"
LUIS = "luis.mora@example.com"
CARLA = "carla.vera@example.com"

USERS = [
    {"email": ANA, "name": "Ana Lima", "dept": "Investigación"},
    {"email": LUIS, "name": "Luis Mora", "dept": "Acuicultura"},
    {"email": CARLA, "name": "Carla Vera", "dept": "Ciencia de datos"},
    {
        "email": "pedro.rios@example.com",
        "name": "Pedro Ríos",
        "dept": "Acuicultura",
        "status": User.UserStatus.INACTIVE,
    },
]

TILAPIA_AUDIO = "s3://biogestor-seed/tilapia/audio/batch-001/"
SHRIMP_AUDIO = "s3://biogestor-seed/camaron/audio/batch-002/"
SHRIMP_IMAGES = "s3://biogestor-seed/camaron/images/weight-b1/"
SHRIMP_VIDEO = "s3://biogestor-seed/camaron/video/behavior-c1/"
OXYGEN_CSV = "s3://biogestor-seed/calidad-agua/oxigeno-2024.csv"
FIELD_NOTES = "s3://biogestor-seed/notas/campo-2023/"

DATASETS = [
    {
        "s3_uri": TILAPIA_AUDIO,
        "name": "Lote de audio de tilapia 001",
        "type": Dataset.DatasetType.AUDIO,
        "owner_email": ANA,
        "description": "Grabaciones de alimentación de tilapia (datos ficticios).",
        "species": "Tilapia (Oreochromis niloticus)",
        "farm": "Camaronera Demo Norte",
        "pool": "Piscina A-3",
        "capture_date": date(2024, 10, 12),
        "license": "CC BY 4.0",
        "type_metadata": {"microphone": "Hidrófono genérico", "sample_rate": 44100},
        "file_format": ".WAV",
        "size_bytes": 4_700_000_000,
        "file_count": 1247,
    },
    {
        "s3_uri": SHRIMP_AUDIO,
        "name": "Audio de alimentación de camarón B-2",
        "type": Dataset.DatasetType.AUDIO,
        "owner_email": LUIS,
        "description": "Sonidos de alimentación de camarón blanco (datos ficticios).",
        "species": "Penaeus vannamei",
        "farm": "Camaronera Demo Sur",
        "pool": "Piscina B-2",
        "capture_date": date(2024, 11, 3),
        "license": "CC BY 4.0",
        "type_metadata": {"microphone": "Hidrófono genérico", "sample_rate": 48000},
        "file_format": ".WAV",
        "size_bytes": 2_100_000_000,
        "file_count": 640,
    },
    {
        "s3_uri": SHRIMP_IMAGES,
        "name": "Imágenes de muestreo de peso B-1",
        "type": Dataset.DatasetType.IMAGE,
        "owner_email": ANA,
        "species": "Penaeus vannamei",
        "farm": "Camaronera Demo Sur",
        "pool": "Piscina B-1",
        "capture_date": date(2025, 1, 20),
        "type_metadata": {"resolution": "1920x1080"},
        "file_format": ".JPG",
        "size_bytes": 850_000_000,
        "file_count": 2300,
    },
    {
        "s3_uri": SHRIMP_VIDEO,
        "name": "Video de comportamiento C-1",
        "type": Dataset.DatasetType.VIDEO,
        "status": Dataset.Status.PROCESSING,
        "owner_email": CARLA,
        "species": "Penaeus vannamei",
        "farm": "Camaronera Demo Norte",
        "pool": "Piscina C-1",
        "capture_date": date(2025, 2, 8),
        "type_metadata": {"resolution": "3840x2160", "fps": 30},
        "file_format": ".MP4",
        "size_bytes": 12_000_000_000,
        "file_count": 18,
    },
    {
        "s3_uri": OXYGEN_CSV,
        "name": "Oxígeno disuelto ciclo 2024",
        "type": Dataset.DatasetType.CSV,
        "owner_email": CARLA,
        "farm": "Camaronera Demo Norte",
        "capture_date": date(2024, 12, 1),
        "type_metadata": {"delimiter": ",", "columns": ["fecha", "piscina", "od_mg_l"]},
        "file_format": ".CSV",
        "size_bytes": 3_400_000,
        "file_count": 1,
    },
    {
        "s3_uri": FIELD_NOTES,
        "name": "Notas de campo ciclo 2023",
        "type": Dataset.DatasetType.TEXT,
        "status": Dataset.Status.ARCHIVED,
        "farm": "Camaronera Demo Sur",
        "capture_date": date(2023, 8, 15),
        "file_format": ".TXT",
        "size_bytes": 120_000,
        "file_count": 35,
    },
]

# (s3_uri del dataset, número de versión, correo del creador)
DATASET_VERSIONS = [
    (TILAPIA_AUDIO, 1, ANA),
    (TILAPIA_AUDIO, 2, ANA),
    (SHRIMP_AUDIO, 1, LUIS),
    (SHRIMP_IMAGES, 1, ANA),
    (SHRIMP_VIDEO, 1, CARLA),
    (OXYGEN_CSV, 1, CARLA),
]

ML_MODELS = [
    {"name": "AquaVoice", "type": "classification", "owner_email": ANA},
    {"name": "ShrimpCounter", "type": "detection", "owner_email": CARLA},
    {"name": "PondSegmenter", "type": "segmentation", "owner_email": LUIS},
]

# (nombre del modelo, versión, estado, métricas, parámetros, creador)
MODEL_VERSIONS = [
    (
        "AquaVoice",
        1,
        "experimental",
        {"accuracy": 0.86, "precision": 0.84, "recall": 0.83, "f1_score": 0.835},
        {"epochs": 30, "learning_rate": 0.001},
        ANA,
    ),
    (
        "AquaVoice",
        2,
        "evaluation",
        {"accuracy": 0.90, "precision": 0.89, "recall": 0.88, "f1_score": 0.885},
        {"epochs": 50, "learning_rate": 0.0005},
        ANA,
    ),
    (
        "AquaVoice",
        3,
        "approved",
        {"accuracy": 0.93, "precision": 0.92, "recall": 0.91, "f1_score": 0.915},
        {"epochs": 80, "learning_rate": 0.0003},
        CARLA,
    ),
    (
        "ShrimpCounter",
        1,
        "approved",
        {"map50": 0.88, "precision": 0.87, "recall": 0.85},
        {"epochs": 100, "image_size": 640},
        CARLA,
    ),
    (
        "PondSegmenter",
        1,
        "experimental",
        {"iou": 0.71, "dice": 0.80},
        {"epochs": 40, "image_size": 512},
        LUIS,
    ),
]

# (modelo, versión, s3_uri del dataset, versión del dataset, uso)
MODEL_VERSION_DATASETS = [
    ("AquaVoice", 1, TILAPIA_AUDIO, 1, "training"),
    ("AquaVoice", 2, TILAPIA_AUDIO, 2, "training"),
    ("AquaVoice", 3, TILAPIA_AUDIO, 2, "training"),
    ("AquaVoice", 3, SHRIMP_AUDIO, 1, "validation"),
    ("ShrimpCounter", 1, SHRIMP_IMAGES, 1, "training"),
    ("PondSegmenter", 1, SHRIMP_VIDEO, 1, "training"),
]

# Clave natural: (versión de dataset, versión de modelo, started_at)
EXPERIMENTS = [
    {
        "model": "AquaVoice",
        "model_version": 3,
        "dataset": SHRIMP_AUDIO,
        "dataset_version": 1,
        "executed_by": CARLA,
        "status": "completed",
        "metrics": {"accuracy": 0.92, "f1_score": 0.91},
        "started_at": utc(2025, 3, 10, 14, 0),
        "finished_at": utc(2025, 3, 10, 14, 42),
    },
    {
        "model": "AquaVoice",
        "model_version": 2,
        "dataset": TILAPIA_AUDIO,
        "dataset_version": 2,
        "executed_by": ANA,
        "status": "completed",
        "metrics": {"accuracy": 0.89, "f1_score": 0.88},
        "started_at": utc(2025, 3, 12, 9, 30),
        "finished_at": utc(2025, 3, 12, 10, 5),
    },
    {
        "model": "ShrimpCounter",
        "model_version": 1,
        "dataset": SHRIMP_IMAGES,
        "dataset_version": 1,
        "executed_by": CARLA,
        "status": "running",
        "metrics": {},
        "started_at": utc(2025, 3, 15, 16, 0),
        "finished_at": None,
    },
    {
        "model": "PondSegmenter",
        "model_version": 1,
        "dataset": SHRIMP_VIDEO,
        "dataset_version": 1,
        "executed_by": LUIS,
        "status": "failed",
        "metrics": {},
        "started_at": utc(2025, 3, 16, 11, 0),
        "finished_at": utc(2025, 3, 16, 11, 3),
    },
]

# Clave natural: content
OBSERVATIONS = [
    {
        "kind": "recommendation",
        "content": "Se recomienda aumentar el muestreo nocturno en la piscina A-3 (dato ficticio).",
        "author_email": ANA,
        "dataset": TILAPIA_AUDIO,
    },
    {
        "kind": "validation",
        "content": "Las etiquetas del lote B-2 fueron revisadas y validadas (dato ficticio).",
        "author_email": LUIS,
        "dataset": SHRIMP_AUDIO,
    },
    {
        "kind": "incident",
        "content": "Ruido de bomba presente en parte de las grabaciones (dato ficticio).",
        "author_email": CARLA,
        "dataset": SHRIMP_AUDIO,
    },
    {
        "kind": "comment",
        "content": "El video C-1 sigue en procesamiento (dato ficticio).",
        "author_email": CARLA,
        "dataset": SHRIMP_VIDEO,
    },
]


# Seeders. Cada uno devuelve (creados, total) o None si el modelo no existe.


def user(email):
    return User.objects.get(email=email)


def seed_users():
    created_count = 0
    for data in USERS:
        data = dict(data)
        email = data.pop("email")
        _, created = User.objects.update_or_create(email=email, defaults=data)
        created_count += created
    return created_count, len(USERS)


def seed_datasets():
    created_count = 0
    for data in DATASETS:
        data = dict(data)
        s3_uri = data.pop("s3_uri")
        owner_email = data.pop("owner_email", None)
        data["owner"] = user(owner_email) if owner_email else None
        _, created = Dataset.objects.update_or_create(s3_uri=s3_uri, defaults=data)
        created_count += created
    return created_count, len(DATASETS)


def seed_dataset_versions():
    dataset_version_model = get_model_or_none("dataset_version")
    if dataset_version_model is None:
        return None
    created_count = 0
    for s3_uri, number, creator in DATASET_VERSIONS:
        dataset = Dataset.objects.get(s3_uri=s3_uri)
        _, created = dataset_version_model.objects.get_or_create(
            dataset=dataset,
            version_number=number,
            defaults={
                "storage_uri": f"{s3_uri}v{number}/",
                "metadata": dataset.type_metadata or {},
                "checksum": fake_checksum(f"{s3_uri}v{number}"),
                "created_by": user(creator),
            },
        )
        created_count += created
    return created_count, len(DATASET_VERSIONS)


def seed_ml_models():
    ml_model = get_model_or_none("ml_model")
    if ml_model is None:
        return None
    created_count = 0
    for data in ML_MODELS:
        data = dict(data)
        name = data.pop("name")
        data["owner"] = user(data.pop("owner_email"))
        _, created = ml_model.objects.update_or_create(name=name, defaults=data)
        created_count += created
    return created_count, len(ML_MODELS)


def seed_model_versions():
    ml_model = get_model_or_none("ml_model")
    model_version_model = get_model_or_none("model_version")
    if ml_model is None or model_version_model is None:
        return None
    created_count = 0
    for name, number, status, metrics, parameters, creator in MODEL_VERSIONS:
        _, created = model_version_model.objects.get_or_create(
            model=ml_model.objects.get(name=name),
            version_number=number,
            defaults={
                "status": status,
                "metrics": metrics,
                "parameters": parameters,
                "artifact_uri": f"s3://biogestor-seed/modelos/{name.lower()}/v{number}/model.bin",
                "created_by": user(creator),
            },
        )
        created_count += created
    return created_count, len(MODEL_VERSIONS)


def _find_versions(model_name, model_number, s3_uri, dataset_number):
    dataset_version_model = get_model_or_none("dataset_version")
    model_version_model = get_model_or_none("model_version")
    model_version = model_version_model.objects.get(
        model__name=model_name, version_number=model_number
    )
    dataset_version = dataset_version_model.objects.get(
        dataset__s3_uri=s3_uri, version_number=dataset_number
    )
    return model_version, dataset_version


def _versions_available():
    return all(get_model_or_none(key) for key in ("dataset_version", "ml_model", "model_version"))


def seed_model_version_datasets():
    link_model = get_model_or_none("model_version_dataset")
    if link_model is None or not _versions_available():
        return None
    created_count = 0
    for model_name, model_number, s3_uri, dataset_number, usage in MODEL_VERSION_DATASETS:
        model_version, dataset_version = _find_versions(
            model_name, model_number, s3_uri, dataset_number
        )
        _, created = link_model.objects.get_or_create(
            model_version=model_version,
            dataset_version=dataset_version,
            defaults={"usage_type": usage},
        )
        created_count += created
    return created_count, len(MODEL_VERSION_DATASETS)


def seed_experiments():
    experiment_model = get_model_or_none("experiment")
    if experiment_model is None or not _versions_available():
        return None
    created_count = 0
    for data in EXPERIMENTS:
        model_version, dataset_version = _find_versions(
            data["model"], data["model_version"], data["dataset"], data["dataset_version"]
        )
        _, created = experiment_model.objects.get_or_create(
            dataset_version=dataset_version,
            model_version=model_version,
            started_at=data["started_at"],
            defaults={
                "executed_by": user(data["executed_by"]),
                "status": data["status"],
                "metrics": data["metrics"],
                "finished_at": data["finished_at"],
            },
        )
        created_count += created
    return created_count, len(EXPERIMENTS)


def seed_observations():
    observation_model = get_model_or_none("observation")
    if observation_model is None:
        return None
    created_count = 0
    for data in OBSERVATIONS:
        _, created = observation_model.objects.get_or_create(
            content=data["content"],
            defaults={
                "kind": data["kind"],
                "author": user(data["author_email"]),
                "dataset": Dataset.objects.get(s3_uri=data["dataset"]),
            },
        )
        created_count += created
    return created_count, len(OBSERVATIONS)


# Orden de dependencia: usuarios -> datasets -> versiones -> enlaces -> experimentos.
SEEDERS = [
    ("usuarios", seed_users),
    ("datasets", seed_datasets),
    ("versiones de dataset", seed_dataset_versions),
    ("modelos", seed_ml_models),
    ("versiones de modelo", seed_model_versions),
    ("modelo-dataset (versiones)", seed_model_version_datasets),
    ("experimentos", seed_experiments),
    ("observaciones", seed_observations),
]


class Command(BaseCommand):
    help = "Carga datos semilla ficticios para desarrollo (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite ejecutar con DEBUG=False (no usar en producción).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG=False: los datos semilla son solo para desarrollo. "
                "Usa --force si estás seguro."
            )

        with transaction.atomic():
            for label, seeder in SEEDERS:
                result = seeder()
                if result is None:
                    self.stdout.write(
                        self.style.WARNING(f"{label}: omitido (el modelo aún no existe)")
                    )
                    continue
                created, total = result
                self.stdout.write(f"{label}: {created} creados, {total - created} ya existían")

        self.stdout.write(self.style.SUCCESS("Datos semilla cargados."))
