import os
import sys
import django
from unittest.mock import patch

# Configurar el entorno de Django
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append("testserver")

from rest_framework.test import APIClient
from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog
from apps.credentials.models import SunatCredential
from common.encryption import encrypt

def test_idempotency_flow():
    print("\n=== Testing Document Idempotency Flow (Fase 7) ===")
    
    # Configurar empresa y aplicacion cliente
    company, _ = Company.objects.get_or_create(
        ruc="20123456789",
        defaults={"business_name": "Empresa Test SAC"}
    )
    client_app, _ = ClientApp.objects.get_or_create(
        company=company,
        name="Test App"
    )
    
    # Configurar credenciales de SUNAT de prueba en la base de datos
    SunatCredential.objects.get_or_create(
        company=company,
        defaults={
            "sunat_user": "1076337562MODDATOS",
            "sunat_password_encrypted": encrypt("MODDATOS"),
            "environment": SunatCredential.Environment.BETA
        }
    )
    
    # Asegurar que la base de datos este libre de nuestros documentos de prueba
    ElectronicDocument.objects.filter(company=company, series="F001", number=9999).delete()
    ElectronicDocument.objects.filter(company=company, series="F001", number=9998).delete()

    
    client = APIClient()
    client.credentials(HTTP_X_API_KEY=str(client_app.api_key))
    
    payload = {
        "document_type": "01",
        "series": "F001",
        "number": 9999,
        "customer_document_type": "6",
        "customer_document": "20100070970",
        "customer_name": "SUPERMERCADOS PERUANOS SA",
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
    
    idempotency_key = "9c1d0e2f-1234-test"
    url = "/api/documents/"
    
    # Simular la respuesta de SunatClient.send_bill
    mock_send_bill_response = {
        "success": True,
        "sunat_ticket": "CDR_RECEIVED",
        "cdr_bytes": b"fake_cdr_zip",
        "raw_response": "CDR ZIP data"
    }
    
    # CASO 1: POST con nueva clave de idempotencia
    print("\n--- CASO 1: Primera peticion (creacion) ---")
    with patch("apps.sunat.services.client.SunatClient.send_bill") as mock_send:
        mock_send.return_value = mock_send_bill_response
        
        response = client.post(url, payload, format="json", HTTP_X_IDEMPOTENCY_KEY=idempotency_key)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
        
        assert response.status_code == 201
        assert response.json()["idempotent"] is False
        
        doc_id = response.json()["id"]
        doc = ElectronicDocument.objects.get(id=doc_id)
        assert doc.idempotency_key == idempotency_key
        assert doc.sunat_status == ElectronicDocument.SunatStatus.SENT
        
        # Verificar que send_bill fue llamado exactamente una vez
        assert mock_send.call_count == 1
        print("CASE 1 passed successfully!")

    # CASO 2: POST con la misma clave de idempotencia
    print("\n--- CASO 2: Peticion duplicada (hit de idempotencia) ---")
    payload_dup = payload.copy()
    payload_dup["number"] = 9998
    
    with patch("apps.sunat.services.client.SunatClient.send_bill") as mock_send:
        mock_send.return_value = mock_send_bill_response
        
        response = client.post(url, payload_dup, format="json", HTTP_X_IDEMPOTENCY_KEY=idempotency_key)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
        
        assert response.status_code == 200
        assert response.json()["idempotent"] is True
        assert response.json()["id"] == doc_id
        
        # Verificar que send_bill NO fue llamado
        assert mock_send.call_count == 0
        print("CASE 2 & 3 passed successfully! SUNAT was not invoked again.")

    # CASO 4: Verificar que RequestLog registre IDEMPOTENCY_HIT
    print("\n--- CASO 4: Verificacion de RequestLog ---")
    hit_logs = RequestLog.objects.filter(
        electronic_document_id=doc_id,
        operation=RequestLog.Operation.IDEMPOTENCY_HIT
    )
    print(f"Number of IDEMPOTENCY_HIT logs found: {hit_logs.count()}")
    assert hit_logs.count() == 1
    hit_log = hit_logs.first()
    assert hit_log.status == RequestLog.Status.SUCCESS
    assert hit_log.request_payload["idempotency_key"] == idempotency_key
    print("CASE 4 passed successfully!")

    # Limpiar documentos de prueba y logs de solicitudes
    ElectronicDocument.objects.filter(company=company, series="F001", number=9999).delete()
    ElectronicDocument.objects.filter(company=company, series="F001", number=9998).delete()
    print("\nCleaned up test documents. Testing finished successfully!")

if __name__ == "__main__":
    test_idempotency_flow()
