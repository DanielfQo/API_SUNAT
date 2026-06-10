"""
Permisos personalizados para api_sunat.
"""

from rest_framework.permissions import BasePermission


class HasValidApiKey(BasePermission):
    """
    Permite el acceso solo si la petición fue autenticada a través de ApiKeyAuthentication.
    Garantiza que request.auth contenga client_app y company.
    """

    message = "Se requiere una API Key válida para acceder a este recurso."

    def has_permission(self, request, view):
        return (
            request.auth is not None
            and isinstance(request.auth, dict)
            and "client_app" in request.auth
            and "company" in request.auth
        )
