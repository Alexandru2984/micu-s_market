from django.contrib import admin

from .models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("prefix", "name", "user", "is_active", "created_at", "last_used_at")
    list_filter = ("is_active",)
    search_fields = ("prefix", "name", "user__username", "user__email")
    readonly_fields = ("prefix", "hashed_key", "created_at", "last_used_at", "revoked_at")

    def has_add_permission(self, request):
        # Keys are created only through the API so the secret is hashed
        # correctly and shown once; admin can inspect and revoke.
        return False
