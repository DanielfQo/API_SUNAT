"""
Vistas de la API de integracion con SUNAT - endpoints provisionales.

Estos endpoints se implementaran cuando la capa del servicio SUNAT este lista.
"""

import base64
import time
import requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.authentication import ApiKeyAuthentication
from common.permissions import HasValidApiKey
from apps.sunat.services.client import SunatClient
from apps.sunat.services.status_checker import get_status
from apps.requests_log.models import RequestLog


@extend_schema(
    summary="Enviar comprobante a SUNAT",
    description="Envia un comprobante firmado electronicamente a SUNAT. Devuelve el estado de la transaccion.",
    request=None,
    responses={200: dict, 400: dict},
)
class SunatSendDocumentView(APIView):
    """POST /api/sunat/send/ - Enviar comprobante a SUNAT."""

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [HasValidApiKey]

    def post(self, request):
        company = request.auth["company"]
        client_app = request.auth["client_app"]

        filename = request.data.get("fileName")
        content_file_base64 = request.data.get("contentFile")

        if not filename or not content_file_base64:
            return Response(
                {"detail": "Se requieren los campos 'fileName' y 'contentFile'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            zip_bytes = base64.b64decode(content_file_base64)
        except Exception as e:
            return Response(
                {"detail": f"No se pudo decodificar 'contentFile' como base64: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = time.time()

        try:
            client = SunatClient(company)
            result = client.send_bill(zip_bytes, filename)
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            RequestLog.objects.create(
                company=company,
                client_app=client_app,
                operation=RequestLog.Operation.SEND_INVOICE,
                request_payload={"filename": filename, "size": len(zip_bytes)},
                response_payload={"error": str(e)},
                status=RequestLog.Status.FAILED,
                duration_ms=duration,
                error_message=str(e),
            )
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        duration = int((time.time() - start_time) * 1000)

        # Registrar log
        RequestLog.objects.create(
            company=company,
            client_app=client_app,
            operation=RequestLog.Operation.SEND_INVOICE,
            request_payload={"filename": filename, "size": len(zip_bytes)},
            response_payload={
                "success": result.get("success"),
                "sunat_ticket": result.get("sunat_ticket"),
                "has_cdr": result.get("cdr_bytes") is not None,
                "error_code": result.get("error_code"),
                "error_message": result.get("error_message"),
            },
            status=RequestLog.Status.SUCCESS if result.get("success") else RequestLog.Status.FAILED,
            duration_ms=duration,
            error_message=result.get("error_message", ""),
        )

        if not result.get("success"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "success": True,
            "sunat_ticket": result.get("sunat_ticket"),
        }
        if result.get("cdr_bytes"):
            response_data["cdr_file"] = base64.b64encode(result.get("cdr_bytes")).decode("utf-8")

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Consultar ticket en SUNAT",
    description="Consulta el estado de un ticket generado por un envio previo a SUNAT.",
    responses={200: dict, 400: dict},
)
class SunatCheckTicketView(APIView):
    """GET /api/sunat/ticket/<ticket_number>/ - Consultar ticket."""

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [HasValidApiKey]

    def get(self, request, ticket_number):
        company = request.auth["company"]
        client_app = request.auth["client_app"]

        start_time = time.time()

        result = get_status(company, ticket_number)

        duration = int((time.time() - start_time) * 1000)

        # Registrar log
        RequestLog.objects.create(
            company=company,
            client_app=client_app,
            operation=RequestLog.Operation.CHECK_TICKET,
            request_payload={"ticket": ticket_number},
            response_payload={
                "success": result.get("success"),
                "status_code": result.get("status_code"),
                "has_cdr": result.get("content") is not None,
                "error_message": result.get("error_message"),
            },
            status=RequestLog.Status.SUCCESS if result.get("success") else RequestLog.Status.FAILED,
            duration_ms=duration,
            error_message=result.get("error_message", ""),
        )

        if not result.get("success"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "success": True,
            "status_code": result.get("status_code"),
        }
        if result.get("content"):
            response_data["cdr_file"] = base64.b64encode(result.get("content")).decode("utf-8")

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Estado de la conexion con SUNAT",
    description="Obtiene el estado de disponibilidad de los servidores de SUNAT (tanto en produccion como homologacion/beta).",
    responses={200: dict},
)
class SunatStatusView(APIView):
    """GET /api/sunat/status/ - Estado de la conexion con SUNAT."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def _check_url(self, url):
        try:
            response = requests.get(url, timeout=2.0, verify=False)
            # Si responde con cualquier codigo HTTP, el servidor esta arriba
            return "online"
        except Exception:
            return "offline"

    def get(self, request):
        beta_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
        prod_url = "https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService"

        beta_status = self._check_url(beta_url)
        prod_status = self._check_url(prod_url)

        return Response(
            {
                "sunat_beta": beta_status,
                "sunat_production": prod_status,
            },
            status=status.HTTP_200_OK,
        )

