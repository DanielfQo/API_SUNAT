from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from common.authentication import ApiKeyAuthentication
from common.permissions import HasValidApiKey

from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """CRUD completo para empresas."""

    serializer_class = CompanySerializer
    lookup_field = "id"
    authentication_classes = [ApiKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated | HasValidApiKey]

    def get_queryset(self):
        user = self.request.user
        # If user is a logged-in Django user
        if user and user.is_authenticated:
            if user.is_superuser:
                return Company.objects.all()
            return Company.objects.filter(owner=user)
        
        # If authenticated via API key
        if self.request.auth and isinstance(self.request.auth, dict) and "company" in self.request.auth:
            return Company.objects.filter(id=self.request.auth["company"].id)
            
        return Company.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            serializer.save(owner=user)
        else:
            serializer.save()
