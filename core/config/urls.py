from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health_check(request):
    """Sencilla prueba de vida (liveness probe)."""
    return JsonResponse({"status": "ok", "service": "api_sunat"})


urlpatterns = [
    # Estado / Salud
    path("", health_check, name="health-check"),
    # Administración
    path("admin/", admin.site.urls),
    # Esquema OpenAPI y documentación interactiva (Swagger/ReDoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # API REST Principal
    path("api/companies/", include("apps.companies.urls")),
    path("api/client-apps/", include("apps.client_apps.urls")),
    path("api/credentials/", include("apps.credentials.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/request-logs/", include("apps.requests_log.urls")),
    path("api/sunat/", include("apps.sunat.urls")),
]
