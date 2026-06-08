from django.contrib import admin

from .models import SunatCredential


@admin.register(SunatCredential)
class SunatCredentialAdmin(admin.ModelAdmin):
    list_display = ("company", "sunat_user", "environment", "created_at")
    list_filter = ("environment",)
    search_fields = ("company__ruc", "sunat_user")
    readonly_fields = ("id", "created_at", "updated_at")
