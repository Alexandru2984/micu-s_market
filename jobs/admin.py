from django.contrib import admin

from .models import BackgroundJob


@admin.register(BackgroundJob)
class BackgroundJobAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "priority", "attempts", "max_attempts", "run_after", "created_at")
    list_filter = ("status", "name", "created_at")
    search_fields = ("id", "name", "last_error")
    readonly_fields = ("id", "attempts", "locked_by", "locked_at", "started_at", "finished_at", "created_at", "updated_at")
