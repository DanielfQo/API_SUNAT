from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("ruc", "business_name", "owner", "is_active", "created_at")
    search_fields = ("ruc", "business_name", "owner__username")
    list_filter = ("is_active", "owner")
    readonly_fields = ("id", "created_at", "updated_at")
