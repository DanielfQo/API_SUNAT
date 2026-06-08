import os
import sys
import django
import requests

# Setup Django environment
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append("localhost")
settings.ALLOWED_HOSTS.append("testserver")

from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument

def test_document(doc_type, series, number, customer_doc_type, customer_doc, customer_name):
    print(f"\n--- Probando {doc_type} {series}-{number} ---")
    company, created = Company.objects.get_or_create(
        ruc="20123456789",
        defaults={"business_name": "Empresa Test SAC"}
    )
    
    client_app, _ = ClientApp.objects.get_or_create(
        company=company,
        name="ERP Principal",
    )
    
    api_key = client_app.api_key
    
    # Delete preexisting test document to avoid IntegrityError
    ElectronicDocument.objects.filter(company=company, series=series, number=number).delete()
    
    # Payload
    payload = {
        "document_type": doc_type,
        "series": series,
        "number": number,
        "customer_document_type": customer_doc_type,
        "customer_document": customer_doc,
        "customer_name": customer_name,
        "total_amount": "118.00",
        "currency": "PEN",
        "details": [
            {
                "description": "Servicio de Consultoria MVP",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }
    
    url = "http://localhost:8000/api/documents/"
    headers = {
        "X-API-Key": str(api_key),
        "Content-Type": "application/json"
    }
    
    # Send request
    # Note: the Django dev server must be running at localhost:8000 for requests.post to work,
    # or we can mock/call the view directly.
    # To run without starting a dev server, we can use DRF's APIClient!
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(HTTP_X_API_KEY=str(api_key))
    
    response = client.post("/api/documents/", payload, format="json")
    print("API Status Code:", response.status_code)
    print("API Response JSON:", response.json())
    
    if response.status_code == 201:
        doc_id = response.json()["id"]
        doc = ElectronicDocument.objects.get(id=doc_id)
        print("Status in DB:", doc.sunat_status)
        print("Ticket in DB:", doc.sunat_ticket)
        print("Response Code in DB:", doc.sunat_response_code)
        print("XML Path in DB:", doc.xml_path)
        print("ZIP Path in DB:", doc.zip_path)
        print("CDR Path in DB:", doc.cdr_zip_path)
        
        # Verify that paths start with company name 'empresa_test_sac'
        assert doc.xml_path.startswith("empresa_test_sac/xml/")
        assert doc.zip_path.startswith("empresa_test_sac/zip/")
        if doc.cdr_zip_path:
            assert doc.cdr_zip_path.startswith("empresa_test_sac/cdr/")
            
        print("OK: Verification of storage paths passed!")
        
        # Cleanup files from storage to keep workspace clean
        for path in [doc.xml_path, doc.zip_path, doc.cdr_zip_path]:
            if path:
                abs_path = os.path.join(settings.MEDIA_ROOT, path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    
        print("OK: Temporary storage files cleaned up!")
        # Delete doc
        doc.delete()

if __name__ == "__main__":
    # Test Factura
    test_document("01", "F001", "900001", "6", "20100070970", "SUPERMERCADOS PERUANOS SA")
    
    # Test Boleta
    test_document("03", "B001", "900001", "1", "44556677", "JUAN PEREZ")
