import os
import sys
import django
from unittest.mock import patch

# Setup Django environment
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog
from apps.documents.services.document_service import check_status

def test_check_status_flow():
    # Setup mock company and app
    company, _ = Company.objects.get_or_create(
        ruc="20123456789",
        defaults={"business_name": "Empresa Test SAC"}
    )
    client_app, _ = ClientApp.objects.get_or_create(
        company=company,
        name="Test App"
    )
    
    # 1. Create a test document
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

    # Mock responses
    class MockStatus:
        def __init__(self, statusCode, content=None):
            self.statusCode = statusCode
            self.content = content

    class MockResponse:
        def __init__(self, statusCode):
            self.status = MockStatus(statusCode)

    # A. Test SUCCESS -> ACCEPTED (code "0")
    print("\n--- Test A: statusCode '0' (ACCEPTED) ---")
    mock_resp_0 = MockResponse("0")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_0
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")
        
        # Verify log
        last_log = RequestLog.objects.filter(electronic_document=updated_doc).first()
        print(f"RequestLog: operation={last_log.operation}, status={last_log.status}, error={last_log.error_message}")

    # B. Test REJECTION -> REJECTED (code "99")
    print("\n--- Test B: statusCode '99' (REJECTED) ---")
    mock_resp_99 = MockResponse("99")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_99
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")

    # C. Test IN PROCESS -> SENT (code "98")
    print("\n--- Test C: statusCode '98' (SENT/En proceso) ---")
    mock_resp_98 = MockResponse("98")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_98
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")

    # D. Test EXCEPTION -> ERROR
    from zeep.exceptions import Fault
    print("\n--- Test D: SOAP Fault (ERROR) ---")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.side_effect = Fault(message="Ticket no existe", code="Server")
        
        updated_doc = check_status(str(doc.id))
        print(f"Mapped Status: {updated_doc.sunat_status}")
        print(f"Mapped Response Code: {updated_doc.sunat_response_code}")
        print(f"Mapped Description: {updated_doc.sunat_description}")
        
        # Verify log
        last_log = RequestLog.objects.filter(electronic_document=updated_doc).first()
        print(f"RequestLog: operation={last_log.operation}, status={last_log.status}, error={last_log.error_message}")

    # Cleanup
    doc.delete()
    print("\nCleaned up test document.")

if __name__ == "__main__":
    test_check_status_flow()
