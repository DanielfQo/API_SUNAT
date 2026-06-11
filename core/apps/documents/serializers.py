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

    def validate(self, data):
        doc_type = data.get("document_type")
        series = data.get("series", "")
        customer_doc_type = data.get("customer_document_type")
        customer_doc = data.get("customer_document", "")
        total_amount = data.get("total_amount")
        details = data.get("details", [])

        # 1. Validar serie
        if not series or len(series) != 4:
            raise serializers.ValidationError({"series": "La serie debe tener exactamente 4 caracteres."})
        
        if doc_type == "01": # Factura
            if not series.upper().startswith("F"):
                raise serializers.ValidationError({"series": "Para Facturas (tipo 01), la serie debe comenzar con 'F'."})
            if customer_doc_type != "6":
                raise serializers.ValidationError({"customer_document_type": "Para Facturas (tipo 01), el tipo de documento del cliente debe ser RUC (6)."})
        elif doc_type == "03": # Boleta
            if not series.upper().startswith("B"):
                raise serializers.ValidationError({"series": "Para Boletas (tipo 03), la serie debe comenzar con 'B'."})
        else:
            raise serializers.ValidationError({"document_type": "Tipo de documento no soportado. Debe ser 01 (Factura) o 03 (Boleta)."})

        # 2. Validar documento del cliente
        if customer_doc_type == "6": # RUC
            if not customer_doc.isdigit() or len(customer_doc) != 11:
                raise serializers.ValidationError({"customer_document": "El RUC del cliente debe tener exactamente 11 dígitos numéricos."})
        elif customer_doc_type == "1": # DNI
            if not customer_doc.isdigit() or len(customer_doc) != 8:
                raise serializers.ValidationError({"customer_document": "El DNI del cliente debe tener exactamente 8 dígitos numéricos."})

        # 3. Validar monto total
        from decimal import Decimal
        if total_amount is None or Decimal(str(total_amount)) <= 0:
            raise serializers.ValidationError({"total_amount": "El monto total debe ser mayor a cero."})

        # 4. Validar detalles e IGV
        if details:
            sum_details = Decimal('0.00')
            for item in details:
                qty = Decimal(str(item.get('quantity', 1)))
                price = Decimal(str(item.get('unit_price', 0)))
                sum_details += (qty * price)
            
            # El total con IGV es sum_details * 1.18
            expected_total = sum_details * Decimal('1.18')
            diff = abs(Decimal(str(total_amount)) - expected_total)
            if diff > Decimal('0.10'): # Tolerancia por redondeo
                raise serializers.ValidationError({"total_amount": f"El monto total ({total_amount}) no coincide con el total esperado de los detalles con IGV ({expected_total:.2f})."})

        return data


