import os
import sys
import django
import base64
from unittest.mock import patch

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

from django.conf import settings
django.setup()

settings.ALLOWED_HOSTS.append("testserver")

from rest_framework.test import APIClient
from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.credentials.models import SunatCredential
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog
from common.encryption import encrypt

class MockStatus:
    def __init__(self, statusCode, content=None):
        self.statusCode = statusCode
        self.content = content

class MockResponse:
    def __init__(self, statusCode, content=None):
        self.status = MockStatus(statusCode, content)

def run_basic_flow_test():
    print("======================================================================")
    print("INICIANDO PRUEBA UNIFICADA: FLUJO BASICO DE INTEGRACION API SUNAT")
    print("======================================================================\n")

    # Limpiar datos previos del test si existen para evitar conflictos en BD real
    Company.objects.filter(ruc="10763375621").delete()

    client = APIClient()

    # --- PASO 1: Verificar disponibilidad de servidores SUNAT (Publico) ---
    print("[PASO 1] Consultando disponibilidad de servidores SUNAT...")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        response = client.get("/api/sunat/status/")
        print("  - Status Code:", response.status_code)
        print("  - Response JSON:", response.json())
        assert response.status_code == 200
        assert response.json()["sunat_beta"] == "online"
        print("  => Servidores activos y accesibles (Simulado)\n")

    # --- PASO 2: Configurar Tenant (Empresa, Credenciales y Client App) ---
    print("[PASO 2] Configurando empresa, credenciales SOL y credenciales de API Key...")
    company = Company.objects.create(
        ruc="10763375621",
        business_name="Empresa Peruana SAC"
    )
    SunatCredential.objects.create(
        company=company,
        sunat_user="10763375621MODDATOS",
        sunat_password_encrypted=encrypt("MODDATOS"),
        environment=SunatCredential.Environment.BETA
    )
    client_app = ClientApp.objects.create(
        company=company,
        name="ERP System Integration"
    )
    print(f"  - RUC: {company.ruc}")
    print(f"  - API Key Generada: {client_app.api_key}")
    print("  => Tenant configurado exitosamente\n")

    # Configurar las credenciales en el cliente HTTP para las siguientes peticiones
    client.credentials(HTTP_X_API_KEY=str(client_app.api_key))

    # --- PASO 3: Emitir Documento y Enviar a SUNAT (POST /api/documents/) ---
    print("[PASO 3] Creando y enviando factura electronica...")
    invoice_payload = {
        "document_type": "01", # Factura
        "series": "F001",
        "number": 105,
        "customer_document_type": "6",
        "customer_document": "20555555559",
        "customer_name": "Cliente de Prueba S.A.",
        "total_amount": "1500.00",
        "currency": "PEN"
    }

    # Mock del envio SOAP (sendBill)
    mock_cdr_content = b"ZIP_CON_CDR_XML_SUNAT_ACEPTADO"
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.sendBill.return_value = mock_cdr_content
        
        response = client.post("/api/documents/", data=invoice_payload, format="json")
        print("  - Status Code:", response.status_code)
        print("  - Response JSON:", response.json())
        
        assert response.status_code == 201
        assert response.json()["status"] == "SENT"
        
        # Verificar que se creo el registro
        doc = ElectronicDocument.objects.get(id=response.json()["id"])
        print(f"  - UUID Documento en DB: {doc.id}")
        print(f"  - Estado de SUNAT en DB: {doc.sunat_status}")
        print(f"  - Ticket de SUNAT: {doc.sunat_ticket}")
        print("  => Factura firmada, empaquetada en ZIP y enviada a SUNAT con exito\n")

    # --- PASO 4: Consultar Estado de Documento por ID (/api/documents/{id}/check-status/) ---
    print("[PASO 4] Consultando estado del comprobante via su ticket...")
    # Mock de la respuesta getStatus indicando que fue Aceptada (codigo "0")
    mock_get_status_response = MockResponse("0", b"CDR_FINAL_RESPONSE_ZIP")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_get_status_response
        
        url = f"/api/documents/{doc.id}/check-status/"
        response = client.post(url)
        print("  - Status Code:", response.status_code)
        print("  - Response JSON:", response.json())
        
        assert response.status_code == 200
        assert response.json()["status"] == "ACCEPTED"
        assert response.json()["sunat_response_code"] == "0"
        
        # Confirmar en DB
        doc.refresh_from_db()
        print(f"  - Estado Actual en DB: {doc.sunat_status} ({doc.sunat_description})")
        print(f"  - Ruta del CDR guardada: {doc.cdr_zip_path}")
        print("  => Comprobante validado y aceptado por la SUNAT\n")

    # --- PASO 5: Probar Envio Directo de Archivo ZIP (POST /api/sunat/send/) ---
    print("[PASO 5] Probando envio directo de archivo ZIP firmado")
    zip_dummy_content = b"DUMMY_ZIP_DATA"
    send_payload = {
        "fileName": "10763375621-01-F001-999.zip",
        "contentFile": base64.b64encode(zip_dummy_content).decode("utf-8")
    }

    mock_send_bill_response = b"DUMMY_CDR_BYTES_DIRECT"
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.sendBill.return_value = mock_send_bill_response
        
        response = client.post("/api/sunat/send/", data=send_payload, format="json")
        print("  - Status Code:", response.status_code)
        print("  - Response JSON:", response.json())
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["sunat_ticket"] == "CDR_RECEIVED"
        assert "cdr_file" in response.json()
        print("  => Envio directo de ZIP realizado y validado correctamente\n")

    # --- PASO 6: Probar Consulta Directa de Ticket (GET /api/sunat/ticket/<ticket>/) ---
    print("[PASO 6] Probando consulta directa de ticket en SUNAT...")
    mock_get_status_response = MockResponse("0", b"DUMMY_TICKET_CDR_DIRECT")
    with patch("apps.sunat.services.client.Client.service") as mock_service:
        mock_service.getStatus.return_value = mock_get_status_response
        
        ticket_number = "987654321"
        response = client.get(f"/api/sunat/ticket/{ticket_number}/")
        print("  - Status Code:", response.status_code)
        print("  - Response JSON:", response.json())
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["status_code"] == "0"
        assert "cdr_file" in response.json()
        print("  => Consulta directa de ticket completada con exito\n")

    # --- PASO 7: Verificar Auditoria de Peticiones (RequestLog) ---
    print("[PASO 7] Verificando logs de auditoria...")
    logs = RequestLog.objects.filter(company=company)
    print(f"  - Cantidad total de logs registrados para esta empresa: {logs.count()}")
    for idx, log in enumerate(logs, 1):
        print(f"    {idx}. Operacion: {log.operation} | Estado: {log.status} | Error: '{log.error_message}'")
    
    assert logs.count() >= 4
    print("  => Todos los logs de auditoria registrados de forma segura en la base de datos\n")

    print("PRUEBAS PASADAS")

if __name__ == "__main__":
    run_basic_flow_test()
