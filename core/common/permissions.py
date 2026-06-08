"""
Custom permissions for sunat_gateway.
"""

from rest_framework.permissions import BasePermission


class HasValidApiKey(BasePermission):
    """
    Grants access only if request was authenticated via ApiKeyAuthentication.
    Ensures request.auth contains client_app and company.
    """

    message = "Se requiere una API Key válida para acceder a este recurso."

    def has_permission(self, request, view):
        return (
            request.auth is not None
            and isinstance(request.auth, dict)
            and "client_app" in request.auth
            and "company" in request.auth
        )
