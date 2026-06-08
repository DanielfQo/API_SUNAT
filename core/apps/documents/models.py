"""
Modelo ElectronicDocument — representa un comprobante de pago electrónico emitido a la SUNAT.

Abarca: Factura, Boleta de Venta, Nota de Crédito y Nota de Débito.
Realiza el seguimiento completo del ciclo de vida, desde PENDING hasta ACCEPTED/REJECTED/ERROR.
"""

from django.db import models

from common.models import TimestampMixin, UUIDPrimaryKeyMixin


class ElectronicDocument(UUIDPrimaryKeyMixin, TimestampMixin):
    """Comprobante electrónico emitido a SUNAT."""

    class DocumentType(models.TextChoices):
        FACTURA = "01", "Factura"
        BOLETA = "03", "Boleta de Venta"
        NOTA_CREDITO = "07", "Nota de Crédito"
        NOTA_DEBITO = "08", "Nota de Débito"

    class SunatStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        GENERATED = "GENERATED", "Generado"
        SIGNED = "SIGNED", "Firmado"
        SENT = "SENT", "Enviado"
        ACCEPTED = "ACCEPTED", "Aceptado"
        REJECTED = "REJECTED", "Rechazado"
        ERROR = "ERROR", "Error"

    # Relationships
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Empresa emisora",
    )

    # Document identification
    document_type = models.CharField(
        max_length=2,
        choices=DocumentType.choices,
        db_index=True,
        help_text="Tipo de comprobante (código SUNAT)",
    )
    series = models.CharField(
        max_length=4,
        help_text="Serie del comprobante (ej: F001, B001)",
    )
    number = models.PositiveIntegerField(
        help_text="Número correlativo del comprobante",
    )

    # Customer data
    customer_document_type = models.CharField(
        max_length=2,
        blank=True,
        default="",
        help_text="Tipo de documento del cliente (6=RUC, 1=DNI, etc.)",
    )
    customer_document = models.CharField(
        max_length=20,
        help_text="Número de documento del cliente",
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Nombre o razón social del cliente",
    )

    # Amounts
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto total del comprobante",
    )
    currency = models.CharField(
        max_length=3,
        default="PEN",
        help_text="Moneda (ISO 4217)",
    )
    details = models.JSONField(
        default=list,
        help_text="Lista de ítems de la factura/boleta",
    )

    # File paths (relative to MEDIA_ROOT)
    xml_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Ruta del archivo XML firmado",
    )
    zip_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Ruta del archivo ZIP enviado a SUNAT",
    )
    cdr_zip_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Ruta del CDR (Constancia de Recepción)",
    )

    # SUNAT response
    hash = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Hash del documento firmado",
    )
    sunat_ticket = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Ticket de recepción de SUNAT",
    )
    idempotency_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Clave de idempotencia única por empresa",
    )
    sunat_status = models.CharField(
        max_length=20,
        choices=SunatStatus.choices,
        default=SunatStatus.PENDING,
        db_index=True,
        help_text="Estado del comprobante en SUNAT",
    )
    sunat_response_code = models.CharField(
        max_length=10,
        blank=True,
        default="",
        help_text="Código de respuesta de SUNAT",
    )
    sunat_description = models.TextField(
        blank=True,
        default="",
        help_text="Descripción de respuesta de SUNAT",
    )
    sunat_response = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Respuesta completa de SUNAT en JSON",
    )

    class Meta:
        db_table = "electronic_documents"
        verbose_name = "Documento Electrónico"
        verbose_name_plural = "Documentos Electrónicos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "series", "number"],
                name="unique_document_per_company",
            ),
            models.UniqueConstraint(
                fields=["company", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="unique_idempotency_key_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.series}-{self.number} ({self.get_document_type_display()})"

    @property
    def full_number(self):
        """Returns formatted document number: F001-00000001"""
        return f"{self.series}-{self.number:08d}"
