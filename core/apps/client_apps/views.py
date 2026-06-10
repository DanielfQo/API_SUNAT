from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import PermissionDenied
from common.authentication import ApiKeyAuthentication
from common.permissions import HasValidApiKey

from .models import ClientApp
from .serializers import ClientAppCreateSerializer, ClientAppSerializer


class ClientAppViewSet(viewsets.ModelViewSet):
    """CRUD para aplicaciones cliente."""

    serializer_class = ClientAppSerializer
    lookup_field = "id"
    authentication_classes = [ApiKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated | HasValidApiKey]

    def get_serializer_class(self):
        if self.action == "create":
            return ClientAppCreateSerializer
        return ClientAppSerializer

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            if user.is_superuser:
                return ClientApp.objects.select_related("company").all()
            return ClientApp.objects.filter(company__owner=user).select_related("company")
        
        if self.request.auth and isinstance(self.request.auth, dict) and "company" in self.request.auth:
            company = self.request.auth["company"]
            return ClientApp.objects.filter(company=company).select_related("company")
            
        return ClientApp.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            if not user.is_superuser:
                company = serializer.validated_data.get("company")
                if company and company.owner != user:
                    raise PermissionDenied("No tienes permiso para gestionar esta empresa.")
            serializer.save()
        else:
            # Autenticado mediante API key
            company = self.request.auth["company"]
            serializer.save(company=company)
