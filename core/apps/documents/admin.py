from django.contrib import admin

from .models import ElectronicDocument


@admin.register(ElectronicDocument)
class ElectronicDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "full_number",
        "document_type",
        "company",
        "total_amount",
        "sunat_status",
        "created_at",
    )
    search_fields = ("series", "number", "customer_document", "company__ruc")
    list_filter = ("document_type", "sunat_status", "currency")
    readonly_fields = ("id", "created_at", "updated_at")
