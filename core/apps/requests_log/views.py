from rest_framework import mixins, viewsets, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from common.authentication import ApiKeyAuthentication
from common.permissions import HasValidApiKey

from .models import RequestLog
from .serializers import RequestLogSerializer


class RequestLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only viewset for request logs (audit trail — no create/update/delete)."""

    serializer_class = RequestLogSerializer
    lookup_field = "id"
    filterset_fields = ["operation", "status", "company", "client_app"]
    authentication_classes = [ApiKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated | HasValidApiKey]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            if user.is_superuser:
                return RequestLog.objects.select_related("company", "client_app", "electronic_document").all()
            return RequestLog.objects.filter(company__owner=user).select_related("company", "client_app", "electronic_document")
            
        if self.request.auth and isinstance(self.request.auth, dict) and "company" in self.request.auth:
            company = self.request.auth["company"]
            return RequestLog.objects.filter(company=company).select_related("company", "client_app", "electronic_document")
            
        return RequestLog.objects.none()
