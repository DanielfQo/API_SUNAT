"""
Autenticación mediante API Key para api_sunat.

Autentica las peticiones utilizando la cabecera X-API-Key.
Resuelve la clave a un ClientApp y su Company asociada,
haciendo que ambos estén disponibles en request.auth durante el ciclo de vida de la petición.
"""

import logging

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

logger = logging.getLogger(__name__)


class ApiKeyAuthentication(BaseAuthentication):
    """
    Autenticación personalizada mediante la cabecera API Key.

    Espera:
        X-API-Key: <api_key>

    En caso de éxito, establece:
        request.user  → AnonymousUser (sin usuario de Django involucrado)
        request.auth  → diccionario con las instancias de client_app y company
    """

    HEADER_NAME = "HTTP_X_API_KEY"

    def authenticate(self, request):
        api_key = request.META.get(self.HEADER_NAME)

        if not api_key:
            return None  # Permite que otros autenticadores lo intenten

        from apps.client_apps.models import ClientApp

        try:
            client_app = ClientApp.objects.select_related("company").get(
                api_key=api_key,
                is_active=True,
            )
        except ClientApp.DoesNotExist:
            logger.warning("Invalid API key attempt: %s...", api_key[:8])
            raise exceptions.AuthenticationFailed(
                "API key inválida o aplicación desactivada."
            )

        # Verifica que la empresa asociada también esté activa
        if not client_app.company.is_active:
            logger.warning(
                "API key valid but company inactive: %s",
                client_app.company.ruc,
            )
            raise exceptions.AuthenticationFailed(
                "La empresa asociada a esta API key está desactivada."
            )

        auth_context = {
            "client_app": client_app,
            "company": client_app.company,
        }

        return (None, auth_context)

    def authenticate_header(self, request):
        return "X-API-Key"


# Configuración para drf-spectacular
try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = "common.authentication.ApiKeyAuthentication"
        name = "ApiKeyAuth"

        def get_security_definition(self, auto_schema):
            return {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Autenticación mediante cabecera X-API-Key para la API de SUNAT."
            }
except ImportError:
    pass

