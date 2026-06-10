from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.core.exceptions import ValidationError
from common.authentication import ApiKeyAuthentication
from common.permissions import HasValidApiKey

from .models import ElectronicDocument
from .serializers import ElectronicDocumentSerializer, DocumentCreateSerializer
from .services.document_service import create_document, check_status


class ElectronicDocumentViewSet(viewsets.ModelViewSet):
    """CRUD para documentos electrónicos."""

    serializer_class = ElectronicDocumentSerializer
    lookup_field = "id"
    filterset_fields = ["document_type", "sunat_status", "company"]
    authentication_classes = [ApiKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated | HasValidApiKey]

    def get_queryset(self):
        """Asegurar que los documentos listados pertenecen al tenant actual o al owner."""
        user = self.request.user
        if user and user.is_authenticated:
            if user.is_superuser:
                return ElectronicDocument.objects.all().select_related("company")
            return ElectronicDocument.objects.filter(company__owner=user).select_related("company")
            
        if self.request.auth and isinstance(self.request.auth, dict) and "company" in self.request.auth:
            company = self.request.auth["company"]
            return ElectronicDocument.objects.filter(company=company).select_related("company")
            
        return ElectronicDocument.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """
        Interceptar la creacion para orquestar mediante el document_service.
        """
        if not (request.auth and isinstance(request.auth, dict) and "company" in request.auth):
            return Response(
                {"detail": "La creación de documentos requiere autenticación mediante API Key."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = request.auth["company"]
        client_app = request.auth["client_app"]
        
        # Obtener el header de idempotencia (X-Idempotency-Key)
        idempotency_key = request.headers.get("X-Idempotency-Key")
        
        try:
            document, idempotent = create_document(
                company, client_app, serializer.validated_data, idempotency_key=idempotency_key
            )
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # Devuelve id, status y bandera idempotent según la especificación
        return Response({
            "id": document.id,
            "status": document.sunat_status,
            "idempotent": idempotent
        }, status=status.HTTP_200_OK if idempotent else status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="check-status")
    def check_status(self, request, id=None):
        """
        POST /api/documents/{id}/check-status/ — Consultar estado del ticket en SUNAT.
        """
        document = self.get_object()
        
        try:
            document = check_status(str(document.id))
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({
            "id": document.id,
            "status": document.sunat_status,
            "sunat_response_code": document.sunat_response_code,
            "sunat_description": document.sunat_description
        }, status=status.HTTP_200_OK)

