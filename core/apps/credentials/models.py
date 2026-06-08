"""
Modelo SunatCredential — almacena las credenciales cifradas de SUNAT por empresa.

La relación uno a uno (OneToOne) con Company asegura que cada empresa tenga exactamente
un conjunto de credenciales de SUNAT (para el entorno BETA o de PRODUCCIÓN).
"""

from django.db import models

from common.models import TimestampMixin, UUIDPrimaryKeyMixin


class SunatCredential(UUIDPrimaryKeyMixin, TimestampMixin):
    """Credenciales para conectarse a SUNAT en nombre de la empresa."""

    class Environment(models.TextChoices):
        BETA = "BETA", "Beta (pruebas)"
        PRODUCTION = "PRODUCTION", "Producción"

    company = models.OneToOneField(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="sunat_credential",
        help_text="Empresa asociada a estas credenciales",
    )
    sunat_user = models.CharField(
        max_length=100,
        help_text="Usuario SOL de SUNAT",
    )
    sunat_password_encrypted = models.TextField(
        help_text="Contraseña SOL cifrada",
    )
    client_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Client ID para API REST SUNAT (opcional)",
    )
    client_secret_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Client Secret cifrado para API REST SUNAT (opcional)",
    )
    certificate = models.TextField(
        blank=True,
        default="",
        help_text="Certificado digital en base64 (opcional)",
    )
    environment = models.CharField(
        max_length=20,
        choices=Environment.choices,
        default=Environment.BETA,
        help_text="Entorno de SUNAT (BETA o PRODUCTION)",
    )

    class Meta:
        db_table = "sunat_credentials"
        verbose_name = "Credencial SUNAT"
        verbose_name_plural = "Credenciales SUNAT"

    def __str__(self):
        return f"Credenciales {self.environment} - {self.company.ruc}"
