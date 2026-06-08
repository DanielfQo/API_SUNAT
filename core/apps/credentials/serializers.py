from rest_framework import serializers

from common.encryption import encrypt

from .models import SunatCredential


class SunatCredentialSerializer(serializers.ModelSerializer):
    """Read serializer — never exposes any encrypted fields."""

    class Meta:
        model = SunatCredential
        fields = [
            "id",
            "company",
            "sunat_user",
            "client_id",
            "environment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SunatCredentialWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer — accepts plain-text password/secret and encrypts them.

    Fields sunat_password and client_secret are write_only:
    they are never returned in responses.
    """

    sunat_password = serializers.CharField(
        write_only=True,
        help_text="Contraseña SOL de SUNAT (se almacena cifrada)",
    )
    client_secret = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Client Secret OAuth SUNAT (se almacena cifrado)",
    )

    class Meta:
        model = SunatCredential
        fields = [
            "id",
            "company",
            "sunat_user",
            "sunat_password",
            "client_id",
            "client_secret",
            "certificate",
            "environment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _encrypt_fields(self, validated_data: dict) -> dict:
        """Pop plain-text secrets, encrypt them, and set the _encrypted fields."""
        plain_password = validated_data.pop("sunat_password", None)
        if plain_password:
            validated_data["sunat_password_encrypted"] = encrypt(plain_password)

        plain_secret = validated_data.pop("client_secret", None)
        if plain_secret:
            validated_data["client_secret_encrypted"] = encrypt(plain_secret)

        return validated_data

    def create(self, validated_data):
        validated_data = self._encrypt_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._encrypt_fields(validated_data)
        return super().update(instance, validated_data)
