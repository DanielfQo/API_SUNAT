"""
API Key Authentication for sunat_gateway.

Authenticates requests using the X-API-Key header.
Resolves the key to a ClientApp and its associated Company,
making both available on request.auth throughout the request lifecycle.
"""

import logging

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

logger = logging.getLogger(__name__)


class ApiKeyAuthentication(BaseAuthentication):
    """
    Custom authentication via API Key header.

    Expects:
        X-API-Key: <api_key>

    On success, sets:
        request.user  → AnonymousUser (no Django user involved)
        request.auth  → dict with client_app and company instances
    """

    HEADER_NAME = "HTTP_X_API_KEY"

    def authenticate(self, request):
        api_key = request.META.get(self.HEADER_NAME)

        if not api_key:
            return None  # Let other authenticators try

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

        # Check that the parent company is also active
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
