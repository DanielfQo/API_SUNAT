import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Ruta absoluta a core:
core_dir = r"c:\Users\danie\OneDrive\Documentos\api_sunat\core"
if core_dir not in sys.path:
    sys.path.append(core_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth.models import User
from apps.companies.models import Company
from apps.companies.serializers import CompanySerializer
from apps.companies.views import CompanyViewSet
from rest_framework.test import APIRequestFactory, force_authenticate

def test_user_owner_logic():
    print("=== STARTING USER OWNER RELATIONSHIP TESTS ===")
    
    # 1. Limpiar la base de datos para una configuración limpia
    Company.objects.all().delete()
    User.objects.all().delete()
    
    # 2. Crear usuarios
    user_a = User.objects.create_user(username="usera", email="usera@test.com", password="password123")
    user_b = User.objects.create_user(username="userb", email="userb@test.com", password="password123")
    superuser = User.objects.create_superuser(username="admin", email="admin@test.com", password="password123")
    
    print(f"Created users: {user_a.username}, {user_b.username}, {superuser.username} (superuser)")
    
    # 3. Crear empresas a través del ORM
    company_a = Company.objects.create(ruc="20111111111", business_name="Empresa A", owner=user_a)
    company_b = Company.objects.create(ruc="20222222222", business_name="Empresa B", owner=user_b)
    company_no_owner = Company.objects.create(ruc="20333333333", business_name="Empresa sin dueno")
    
    print("Created companies:")
    print(f"  - Company A: {company_a} (Owner: {company_a.owner})")
    print(f"  - Company B: {company_b} (Owner: {company_b.owner})")
    print(f"  - Company No Owner: {company_no_owner} (Owner: {company_no_owner.owner})")
    
    # Comprobar relación de clave foránea (FK)
    assert company_a.owner == user_a
    assert company_b.owner == user_b
    assert company_no_owner.owner is None
    print("OK: ORM fields verified successfully!")
    
    # 4. Probar Serializador
    serializer = CompanySerializer(company_a)
    data = serializer.data
    print("Serialized Company A:", data)
    assert "owner" in data
    assert data["owner"] == user_a.id
    print("OK: Serializer representation verified successfully!")
    
    # 5. Probar el queryset y creación del viewset bajo diferentes usuarios autenticados
    factory = APIRequestFactory()
    
    # Filtrado de querysets de la vista
    # Caso A: autenticado como user_a -> debería ver solo la Empresa A
    request = factory.get("/api/companies/")
    force_authenticate(request, user=user_a)
    view = CompanyViewSet.as_view({'get': 'list'})
    response = view(request)
    print("User A response status:", response.status_code)
    print("User A response data:", response.data)
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['ruc'] == "20111111111"
    print("OK: User A can only see owned company A!")
    
    # Caso B: autenticado como user_b -> debería ver solo la Empresa B
    request = factory.get("/api/companies/")
    force_authenticate(request, user=user_b)
    response = view(request)
    print("User B response data:", response.data)
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['ruc'] == "20222222222"
    print("OK: User B can only see owned company B!")
    
    # Caso C: autenticado como superusuario -> debería ver todas las empresas
    request = factory.get("/api/companies/")
    force_authenticate(request, user=superuser)
    response = view(request)
    print("Superuser response data count:", len(response.data['results']))
    assert response.status_code == 200
    assert len(response.data['results']) == 3
    print("OK: Superuser can see all companies!")
    
    # 6. Probar la creación a través de la API estableciendo automáticamente al dueño
    request = factory.post("/api/companies/", {
        "ruc": "20444444444",
        "business_name": "Empresa C"
    }, format="json")
    force_authenticate(request, user=user_a)
    view_create = CompanyViewSet.as_view({'post': 'create'})
    response = view_create(request)
    print("Creation response status:", response.status_code)
    print("Creation response data:", response.data)
    assert response.status_code == 201
    
    created_company = Company.objects.get(ruc="20444444444")
    assert created_company.owner == user_a
    print("OK: New company created via viewset automatically assigned User A as owner!")
    
    # 7. Limpiar registros de prueba
    Company.objects.all().delete()
    User.objects.all().delete()
    print("=== ALL TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_user_owner_logic()
