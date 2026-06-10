"""
Mixins de modelos compartidos para api_sunat.
"""

import uuid

from django.db import models


class TimestampMixin(models.Model):
    """Añade los campos created_at y updated_at con gestión automática."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPrimaryKeyMixin(models.Model):
    """Usa UUID como clave primaria en lugar de un entero autoincrementable."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
