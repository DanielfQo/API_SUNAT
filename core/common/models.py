"""
Shared model mixins for sunat_gateway.
"""

import uuid

from django.db import models


class TimestampMixin(models.Model):
    """Adds created_at and updated_at fields with automatic management."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPrimaryKeyMixin(models.Model):
    """Uses UUID as primary key instead of auto-incrementing integer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
