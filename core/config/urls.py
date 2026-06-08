from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Simple liveness probe."""
    return JsonResponse({"status": "ok", "service": "api_sunat"})


urlpatterns = [
    # Health / liveness
    path("", health_check, name="health-check"),
    # Admin
    path("admin/", admin.site.urls),
    # Core REST API
    path("api/companies/", include("apps.companies.urls")),
    path("api/client-apps/", include("apps.client_apps.urls")),
    path("api/credentials/", include("apps.credentials.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/request-logs/", include("apps.requests_log.urls")),
    path("api/sunat/", include("apps.sunat.urls")),
]
