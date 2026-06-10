import os
import sys
import django
from unittest.mock import patch

# Configurar el entorno de Django
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog
from apps.documents.services.document_service import check_status

def test_check_status_flow():
    # Configurar empresa y aplicación simuladas
    company, _ = Company.objects.get_or_create(
        ruc="20123456789",
        defaults={"business_name": "Empresa Test SAC"}
    )
    client_app, _ = ClientApp.objects.get_or_create(
        company=company,
        name="Test App"
    )
    
    # 1. Crear un documento de prueba
    doc = ElectronicDocument.objects.create(
        company=company,
        document_type=ElectronicDocument.DocumentType.FACTURA,
        series="F001",
        number=999,
        customer_document_type="6",
        customer_document="20100070970",
        total_amount=100.00,
        sunat_ticket="123456789",
        sunat_status=ElectronicDocument.SunatStatus.SENT
    )
    print(f"Created test document with ID: {doc.id}, ticket: {doc.sunat_ticket}, status: {doc.sunat_status}")

    # Respuestas simuladas
    class MockStatus:
        def __init__(self, statusCode, content=None):
            self.statusCode = statusCode
            self.content = content

    class MockResponse:
        def __init__(self, statusCode):
            self.status = MockStatus(statusCode)

    # A. Probar ÉXITO -> ACEPTADO (código "0")
    print("\n--- Test A: statusCode '0' (ACCEPTED) ---")
    mock_resp_0 = MockResponse("0")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_0
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")
        
        # Verificar log
        last_log = RequestLog.objects.filter(electronic_document=updated_doc).first()
        print(f"RequestLog: operation={last_log.operation}, status={last_log.status}, error={last_log.error_message}")

    # B. Probar RECHAZO -> RECHAZADO (código "99")
    print("\n--- Test B: statusCode '99' (REJECTED) ---")
    mock_resp_99 = MockResponse("99")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_99
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")

    # C. Probar EN PROCESO -> ENVIADO (código "98")
    print("\n--- Test C: statusCode '98' (SENT/En proceso) ---")
    mock_resp_98 = MockResponse("98")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_98
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")

    # D. Probar EXCEPCIÓN -> ERROR
    from zeep.exceptions import Fault
    print("\n--- Test D: SOAP Fault (ERROR) ---")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.side_effect = Fault(message="Ticket no existe", code="Server")
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")
        
        # Verificar log
        last_log = RequestLog.objects.filter(electronic_document=updated_doc).first()
        print(f"RequestLog: operation={last_log.operation}, status={last_log.status}, error={last_log.error_message}")

    # Limpieza
    doc.delete()
    print("\nCleaned up test document.")

if __name__ == "__main__":
    test_check_status_flow()
