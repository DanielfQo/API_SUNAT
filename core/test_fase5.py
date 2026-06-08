import os
import sys
import django
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

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
        name="Test App",
    )
    
    api_key = client_app.api_key
    
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
    
    response = requests.post(url, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
    if response.status_code == 201:
        doc_id = response.json()["id"]
        doc = ElectronicDocument.objects.get(id=doc_id)
        print("Status:", doc.sunat_status)
        print("Ticket:", doc.sunat_ticket)
        print("Response Code:", doc.sunat_response_code)
        if doc.sunat_response and 'error' in doc.sunat_response:
            print("Response Error:", doc.sunat_response['error'])

if __name__ == "__main__":
    # Test Factura
    test_document("01", "F001", "00000019", "6", "20100070970", "SUPERMERCADOS PERUANOS SA")
    
    # Test Boleta
    test_document("03", "B001", "00000007", "1", "44556677", "JUAN PEREZ")
