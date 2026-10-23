"""Catálogo de datasets."""

from django.conf import settings
from django.db import models
from django.db.models.functions import Now


class Dataset(models.Model):
    """Conjunto de datos registrado en BioGestor.

    BioGestor no sube ni copia archivos: solo guarda la referencia a un objeto
    o carpeta que ya existe en S3, junto con su metadata.
    """

    class Tipo(models.TextChoices):
        AUDIO = "audio", "Audio"
        IMAGEN = "imagen", "Imagen"
        VIDEO = "video", "Video"
        CSV = "csv", "CSV"
        TEXTO = "texto", "Texto"
        OTRO = "otro", "Otro"

    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        PROCESANDO = "procesando", "Procesando"
        ARCHIVADO = "archivado", "Archivado"
        ERROR = "error", "Error"

    # Obligatorios según el PO
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    # Listado del prototipo: Nombre, Tipo, Investigador, Fecha de registro, Estado
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="datasets",
        verbose_name="investigador responsable",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Detalle del prototipo: Metadatos
    descripcion = models.TextField(blank=True)
    especie = models.CharField(max_length=100, blank=True)
    granja = models.CharField(max_length=100, blank=True)
    piscina = models.CharField(max_length=50, blank=True)
    fecha_captura = models.DateField(null=True, blank=True)
    licencia = models.CharField(max_length=100, blank=True)
    # Campos que cambian según el tipo (micrófono, frecuencia de muestreo, resolución...)
    metadatos_tipo = models.JSONField(default=dict, blank=True)

    # Detalle del prototipo: Almacenamiento
    ubicacion_s3 = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Referencia a un objeto o carpeta existente, por ejemplo s3://bucket/carpeta/",
    )
    formato = models.CharField(max_length=30, blank=True)
    tamano_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    cantidad_archivos = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_registro"]
        constraints = [
            # La misma referencia de S3 no se puede registrar dos veces.
            models.UniqueConstraint(
                fields=["ubicacion_s3"],
                condition=~models.Q(ubicacion_s3=""),
                name="dataset_ubicacion_s3_unica",
            ),
            # Solo referencias a S3 (o vacío mientras no se conozca).
            models.CheckConstraint(
                condition=models.Q(ubicacion_s3="") | models.Q(ubicacion_s3__startswith="s3://"),
                name="dataset_ubicacion_s3_formato",
            ),
            models.CheckConstraint(
                condition=models.Q(fecha_captura__isnull=True) | models.Q(fecha_captura__lte=Now()),
                name="dataset_fecha_captura_no_futura",
            ),
        ]

    def save(self, *args, **kwargs):
        # " s3://x " y "s3://x" deben contar como la misma referencia.
        self.ubicacion_s3 = self.ubicacion_s3.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
