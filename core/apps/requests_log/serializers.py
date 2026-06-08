from rest_framework import serializers

from .models import RequestLog


class RequestLogSerializer(serializers.ModelSerializer):
    operation_display = serializers.CharField(
        source="get_operation_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = RequestLog
        fields = [
            "id",
            "company",
            "client_app",
            "electronic_document",
            "operation",
            "operation_display",
            "request_payload",
            "response_payload",
            "status",
            "status_display",
            "duration_ms",
            "error_message",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
