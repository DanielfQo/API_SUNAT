import os
import sys
import django
from unittest.mock import patch

# Setup Django environment
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append("testserver")

from rest_framework.test import APIClient
from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument

def test_check_status_api():
    # Setup mock company and app
    company, _ = Company.objects.get_or_create(
        ruc="20123456789",
        defaults={"business_name": "Empresa Test SAC"}
    )
    client_app, _ = ClientApp.objects.get_or_create(
        company=company,
        name="Test App"
    )
    
    # Delete preexisting test document to avoid IntegrityError on retry
    ElectronicDocument.objects.filter(company=company, series="F001", number=999).delete()
    
    # Create a test document
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

    class MockStatus:
        def __init__(self, statusCode, content=None):
            self.statusCode = statusCode
            self.content = content

    class MockResponse:
        def __init__(self, statusCode, content=None):
            self.status = MockStatus(statusCode, content)

    client = APIClient()
    # Add API Key authentication header
    client.credentials(HTTP_X_API_KEY=str(client_app.api_key))
    
    url = f"/api/documents/{doc.id}/check-status/"
    print(f"Testing URL: {url}")
    
    mock_resp_0 = MockResponse("0", b"DUMMY_CDR_ZIP_CONTENT")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_resp_0
        
        response = client.post(url)
        print("API Status Code:", response.status_code)
        print("API Response JSON:", response.json())
        
        # Asserts
        assert response.status_code == 200
        assert response.json()["status"] == "ACCEPTED"
        assert response.json()["sunat_response_code"] == "0"
        assert response.json()["sunat_description"] == "Aceptado"
        print("Assertion passed for ACCEPTED!")
        
        # Verify CDR was saved in DB
        doc.refresh_from_db()
        print("CDR ZIP Path in DB:", doc.cdr_zip_path)
        assert doc.cdr_zip_path != ""
        # The path should now start with company folder name 'empresa_test_sac/cdr/'
        assert doc.cdr_zip_path.startswith("empresa_test_sac/cdr/")
        assert doc.cdr_zip_path.endswith(".zip")
        print("Assertion passed for CDR saving in new storage structure!")
        
        # Cleanup file from filesystem
        if doc.cdr_zip_path:
            abs_path = os.path.join(settings.MEDIA_ROOT, doc.cdr_zip_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print("Cleaned up CDR file from storage.")

    # Cleanup
    doc.delete()
    print("Cleaned up test document.")

if __name__ == "__main__":
    test_check_status_api()
