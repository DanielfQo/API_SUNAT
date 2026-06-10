"""
Modelo ClientApp — representa una aplicación consumidora de la API.

Cada empresa puede registrar múltiples aplicaciones (ERP, POS, Ecommerce, etc.)
que consumen la API de la pasarela. Cada app obtiene su propio par de api_key/api_secret.
"""

import secrets

from django.db import models

from common.models import TimestampMixin, UUIDPrimaryKeyMixin


def generate_api_key():
    """Genera una clave de API aleatoria segura (48 caracteres)."""
    return secrets.token_urlsafe(36)


def generate_api_secret():
    """Genera un secreto de API aleatorio seguro (64 caracteres)."""
    return secrets.token_urlsafe(48)


class ClientApp(UUIDPrimaryKeyMixin, TimestampMixin):
    """Aplicación que consume la API de api_sunat."""

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="client_apps",
        help_text="Empresa propietaria de esta aplicación",
    )
    name = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo de la aplicación (ej: ERP, POS)",
    )
    api_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        default=generate_api_key,
        help_text="Clave pública de la API",
    )
    api_secret = models.CharField(
        max_length=100,
        default=generate_api_secret,
        help_text="Clave secreta de la API (mostrar solo al crear)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si la aplicación puede hacer requests",
    )

    class Meta:
        db_table = "client_apps"
        verbose_name = "Aplicación Cliente"
        verbose_name_plural = "Aplicaciones Cliente"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.company.ruc})"

    def regenerate_keys(self):
        """Regenera tanto la clave API como el secreto."""
        self.api_key = generate_api_key()
        self.api_secret = generate_api_secret()
        self.save(update_fields=["api_key", "api_secret", "updated_at"])
