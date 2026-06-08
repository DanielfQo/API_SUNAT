from rest_framework import serializers

from .models import ClientApp


class ClientAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientApp
        fields = [
            "id",
            "company",
            "name",
            "api_key",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "api_key", "created_at", "updated_at"]


class ClientAppCreateSerializer(serializers.ModelSerializer):
    """Retorna el api_secret únicamente en la creación."""

    class Meta:
        model = ClientApp
        fields = [
            "id",
            "company",
            "name",
            "api_key",
            "api_secret",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "api_key", "api_secret", "created_at"]
