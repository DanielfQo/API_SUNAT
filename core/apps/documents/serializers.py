from rest_framework import serializers

from .models import ElectronicDocument


class ElectronicDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(
        source="get_document_type_display", read_only=True
    )
    sunat_status_display = serializers.CharField(
        source="get_sunat_status_display", read_only=True
    )
    full_number = serializers.CharField(read_only=True)

    class Meta:
        model = ElectronicDocument
        fields = [
            "id",
            "company",
            "document_type",
            "document_type_display",
            "series",
            "number",
            "full_number",
            "customer_document_type",
            "customer_document",
            "customer_name",
            "total_amount",
            "currency",
            "details",
            "xml_path",
            "zip_path",
            "cdr_zip_path",
            "hash",
            "sunat_ticket",
            "idempotency_key",
            "sunat_status",
            "sunat_status_display",
            "sunat_response_code",
            "sunat_description",
            "sunat_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "xml_path",
            "zip_path",
            "cdr_zip_path",
            "hash",
            "sunat_ticket",
            "idempotency_key",
            "sunat_status",
            "sunat_response_code",
            "sunat_description",
            "sunat_response",
            "created_at",
            "updated_at",
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para el POST /api/documents/.
    Solo expone los campos necesarios para crear un documento.
    El id y sunat_status se devuelven en la respuesta (read_only).
    """
    status = serializers.CharField(source="sunat_status", read_only=True)

    class Meta:
        model = ElectronicDocument
        fields = [
            "id",
            "document_type",
            "series",
            "number",
            "customer_document_type",
            "customer_document",
            "customer_name",
            "total_amount",
            "currency",
            "details",
            "status",
        ]
        read_only_fields = ["id", "status"]

