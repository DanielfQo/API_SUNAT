from django.contrib import admin

from .models import ClientApp


@admin.register(ClientApp)
class ClientAppAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "is_active", "created_at")
    search_fields = ("name", "company__ruc", "company__business_name")
    list_filter = ("is_active",)
    readonly_fields = ("id", "api_key", "api_secret", "created_at", "updated_at")
