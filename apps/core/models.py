"""Registro sintético para la prueba de integración del Sprint 0."""

from django.db import models


class IntegrationProbe(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    message = models.CharField(max_length=200)
