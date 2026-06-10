"""
Vistas de la API de integración con SUNAT — endpoints provisionales.

Estos endpoints se implementarán cuando la capa del servicio SUNAT esté lista.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class SunatSendDocumentView(APIView):
    """POST /api/sunat/send/ — Enviar comprobante a SUNAT."""

    def post(self, request):
        return Response(
            {"detail": "Endpoint de envío a SUNAT — pendiente de implementación."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class SunatCheckTicketView(APIView):
    """GET /api/sunat/ticket/<ticket_number>/ — Consultar ticket."""

    def get(self, request, ticket_number):
        return Response(
            {"detail": "Consulta de ticket — pendiente de implementación."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
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
