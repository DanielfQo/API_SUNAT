"""
Vistas de la API de integración con SUNAT — endpoints provisionales.

Estos endpoints se implementarán cuando la capa del servicio SUNAT esté lista.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema


@extend_schema(
    summary="Enviar comprobante a SUNAT",
    description="Envía un comprobante firmado electrónicamente a SUNAT. Devuelve el estado de la transacción.",
    request=None,
    responses={501: dict},
)
class SunatSendDocumentView(APIView):
    """POST /api/sunat/send/ — Enviar comprobante a SUNAT."""

    def post(self, request):
        return Response(
            {"detail": "Endpoint de envío a SUNAT — pendiente de implementación."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


@extend_schema(
    summary="Consultar ticket en SUNAT",
    description="Consulta el estado de un ticket generado por un envío previo a SUNAT.",
    responses={501: dict},
)
class SunatCheckTicketView(APIView):
    """GET /api/sunat/ticket/<ticket_number>/ — Consultar ticket."""

    def get(self, request, ticket_number):
        return Response(
            {"detail": "Consulta de ticket — pendiente de implementación."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


@extend_schema(
    summary="Estado de la conexión con SUNAT",
    description="Obtiene el estado de disponibilidad de los servidores de SUNAT (tanto en producción como homologación/beta).",
    responses={200: dict},
)
class SunatStatusView(APIView):
    """GET /api/sunat/status/ — Estado de la conexión con SUNAT."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "sunat_beta": "placeholder",
                "sunat_production": "placeholder",
                "detail": "Verificación de estado de SUNAT — pendiente de implementación.",
            },
            status=status.HTTP_200_OK,
        )

