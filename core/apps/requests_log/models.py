"""
Modelo RequestLog — historial de auditoría de todas las llamadas a la API de SUNAT.

Registra cada operación (SEND_INVOICE, CHECK_TICKET, CONSULT_RUC, etc.)
con los payloads de solicitud/respuesta completos para depuración y conformidad.
"""

from django.db import models

from common.models import TimestampMixin, UUIDPrimaryKeyMixin


class RequestLog(UUIDPrimaryKeyMixin, TimestampMixin):
    """Registro técnico de llamadas realizadas a SUNAT."""

    class Operation(models.TextChoices):
        SEND_INVOICE = "SEND_INVOICE", "Enviar Comprobante"
        CHECK_TICKET = "CHECK_TICKET", "Consultar Ticket"
        DOWNLOAD_CDR = "DOWNLOAD_CDR", "Descargar CDR"
        CONSULT_RUC = "CONSULT_RUC", "Consultar RUC"
        CONSULT_DNI = "CONSULT_DNI", "Consultar DNI"
        VOID_DOCUMENT = "VOID_DOCUMENT", "Anular Documento"
        GET_STATUS = "GET_STATUS", "Obtener Estado"
        IDEMPOTENCY_HIT = "IDEMPOTENCY_HIT", "Hit de Idempotencia"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Exitoso"
        FAILED = "FAILED", "Fallido"
        PENDING = "PENDING", "Pendiente"

    # Relaciones
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="request_logs",
        help_text="Empresa que realizó la solicitud",
    )
    client_app = models.ForeignKey(
        "client_apps.ClientApp",
        on_delete=models.CASCADE,
        related_name="request_logs",
        help_text="Aplicación que originó la solicitud",
    )
    electronic_document = models.ForeignKey(
        "documents.ElectronicDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_logs",
        help_text="Documento asociado (si aplica)",
    )

    # Detalles de la operación
    operation = models.CharField(
        max_length=30,
        choices=Operation.choices,
        db_index=True,
        help_text="Tipo de operación realizada",
    )
    request_payload = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Payload enviado a SUNAT",
    )
    response_payload = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Respuesta recibida de SUNAT",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Estado de la solicitud",
    )
    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duración de la llamada en milisegundos",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Mensaje de error (si falló)",
    )

    class Meta:
        db_table = "request_logs"
        verbose_name = "Log de Solicitud"
        verbose_name_plural = "Logs de Solicitudes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.operation} - {self.status} ({self.company.ruc})"
