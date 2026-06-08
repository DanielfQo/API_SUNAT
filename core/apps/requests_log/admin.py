from django.contrib import admin

from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("operation", "status", "company", "client_app", "duration_ms", "created_at")
    search_fields = ("company__ruc", "operation")
    list_filter = ("operation", "status")
    readonly_fields = (
        "id",
        "company",
        "client_app",
        "electronic_document",
        "operation",
        "request_payload",
        "response_payload",
        "status",
        "duration_ms",
        "error_message",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
