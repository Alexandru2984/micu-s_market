from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "object_type", "object_id", "ip_address", "request_id", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("actor__username", "actor__email", "object_type", "object_id", "request_id", "ip_address")
    readonly_fields = (
        "actor",
        "event_type",
        "object_type",
        "object_id",
        "request_id",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
