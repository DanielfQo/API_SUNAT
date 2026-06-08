"""
Modelo de Empresa — representa un inquilino (tenant) en la plataforma.

Cada empresa se identifica por su RUC y puede tener múltiples
aplicaciones cliente, credenciales, documentos e historiales de solicitudes.
"""

from django.conf import settings
from django.db import models

from common.models import TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin):
    """Empresa registrada en la plataforma."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="companies",
        null=True,
        blank=True,
        help_text="Usuario dueño de la empresa",
    )

    ruc = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        help_text="RUC de la empresa (11 dígitos)",
    )
    business_name = models.CharField(
        max_length=255,
        help_text="Razón social de la empresa",
    )
    trade_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Nombre comercial (opcional)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si la empresa está activa en la plataforma",
    )

    class Meta:
        db_table = "companies"
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ruc} - {self.business_name}"
