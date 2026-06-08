import os
import sys
import django

# Setup Django environment
sys.path.append("c:/Users/danie/OneDrive/Documentos/api_sunat/core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append("testserver")

from django.contrib.auth.models import User
from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.credentials.models import SunatCredential
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog

from rest_framework.test import APIClient

def test_viewsets_isolation():
    print("=== STARTING VIEWSET TENANT ISOLATION TESTS ===")
    
    # Clean DB
    RequestLog.objects.all().delete()
    ElectronicDocument.objects.all().delete()
    SunatCredential.objects.all().delete()
    ClientApp.objects.all().delete()
    Company.objects.all().delete()
    User.objects.all().delete()
    
    # 1. Create Users
    user_a = User.objects.create_user(username="usera", email="usera@test.com", password="password123")
    user_b = User.objects.create_user(username="userb", email="userb@test.com", password="password123")
    
    # 2. Create Companies owned by each user
    company_a = Company.objects.create(ruc="20111111111", business_name="Empresa A", owner=user_a)
    company_b = Company.objects.create(ruc="20222222222", business_name="Empresa B", owner=user_b)
    
    # 3. Create Client Apps for each company
    app_a = ClientApp.objects.create(company=company_a, name="App Company A")
    app_b = ClientApp.objects.create(company=company_b, name="App Company B")
    
    # 4. Create Sunat Credentials for each company
    cred_a = SunatCredential.objects.create(company=company_a, sunat_user="USERA", sunat_password_encrypted="CIPHERED_A")
    cred_b = SunatCredential.objects.create(company=company_b, sunat_user="USERB", sunat_password_encrypted="CIPHERED_B")
    
    # 5. Create Documents for each company
    doc_a = ElectronicDocument.objects.create(
        company=company_a, document_type="01", series="F001", number=1, customer_document="123", total_amount=10
    )
    doc_b = ElectronicDocument.objects.create(
        company=company_b, document_type="01", series="F001", number=2, customer_document="456", total_amount=20
    )
    
    # 6. Create Request Logs for each company
    log_a = RequestLog.objects.create(
        company=company_a, client_app=app_a, electronic_document=doc_a,
        operation=RequestLog.Operation.SEND_INVOICE, status=RequestLog.Status.SUCCESS
    )
    log_b = RequestLog.objects.create(
        company=company_b, client_app=app_b, electronic_document=doc_b,
        operation=RequestLog.Operation.SEND_INVOICE, status=RequestLog.Status.SUCCESS
    )
    
    # --- TEST A: User A authenticated requests (Session/Basic Auth) ---
    print("\n--- Test A: User A (should see only Company A details) ---")
    client_user_a = APIClient()
    client_user_a.force_authenticate(user=user_a)
    
    # Client Apps list
    response = client_user_a.get("/api/client-apps/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['name'] == "App Company A"
    print("OK: User A only sees Client App A")
    
    # Sunat Credentials list
    response = client_user_a.get("/api/credentials/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['sunat_user'] == "USERA"
    print("OK: User A only sees Credentials A")
    
    # Documents list
    response = client_user_a.get("/api/documents/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['number'] == 1
    print("OK: User A only sees Documents A")
    
    # Request Logs list
    response = client_user_a.get("/api/request-logs/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert str(response.json()['results'][0]['electronic_document']) == str(doc_a.id)
    print("OK: User A only sees Request Logs A")
    
    # --- TEST B: API Key (Client App B) authenticated requests ---
    print("\n--- Test B: API Key of App B (should see only Company B details) ---")
    client_api_b = APIClient()
    client_api_b.credentials(HTTP_X_API_KEY=str(app_b.api_key))
    
    # Client Apps list
    response = client_api_b.get("/api/client-apps/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['name'] == "App Company B"
    print("OK: API Key B only sees Client App B")
    
    # Sunat Credentials list
    response = client_api_b.get("/api/credentials/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['sunat_user'] == "USERB"
    print("OK: API Key B only sees Credentials B")
    
    # Documents list
    response = client_api_b.get("/api/documents/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['number'] == 2
    print("OK: API Key B only sees Documents B")
    
    # Request Logs list
    response = client_api_b.get("/api/request-logs/")
    assert response.status_code == 200
    assert len(response.json()['results']) == 1
    assert str(response.json()['results'][0]['electronic_document']) == str(doc_b.id)
    print("OK: API Key B only sees Request Logs B")
    
    # Clean DB
    RequestLog.objects.all().delete()
    ElectronicDocument.objects.all().delete()
    SunatCredential.objects.all().delete()
    ClientApp.objects.all().delete()
    Company.objects.all().delete()
    User.objects.all().delete()
    print("\n=== ALL ISOLATION TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_viewsets_isolation()
