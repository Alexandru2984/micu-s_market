from django.contrib import admin
from audit.utils import audit_log
from .models import UserProfile, UserReport, UserStrike


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "verification_status",
        "is_verified",
        "verification_requested_at",
        "updated_at",
    )
    list_filter = ("verification_status", "is_verified", "created_at")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "phone", "city")
    readonly_fields = ("created_at", "updated_at", "verification_requested_at", "verification_reviewed_at")
    actions = ("approve_profiles", "reject_profiles")

    fieldsets = (
        ("Utilizator", {
            "fields": ("user", "avatar", "bio", "phone", "city", "county", "date_of_birth"),
        }),
        ("Verificare", {
            "fields": (
                "is_verified",
                "verification_status",
                "verification_requested_at",
                "verification_reviewed_at",
                "verification_note",
            ),
        }),
        ("Statistici", {
            "fields": ("total_listings", "total_sales", "average_rating"),
        }),
        ("Sistem", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.action(description="Aprobă verificarea")
    def approve_profiles(self, request, queryset):
        for profile in queryset:
            profile.approve_verification()
            audit_log("profile.verification_approved", request=request, obj=profile)

    @admin.action(description="Respinge verificarea")
    def reject_profiles(self, request, queryset):
        for profile in queryset:
            profile.reject_verification("Respins din admin.")
            audit_log("profile.verification_rejected", request=request, obj=profile)


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("reported_user", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("reported_user__username", "reporter__username", "details", "moderator_note")
    readonly_fields = ("reported_user", "reporter", "reason", "details", "created_at", "updated_at")
    actions = ("mark_reviewed", "mark_dismissed", "mark_action_taken")

    @admin.action(description="Marchează ca verificat")
    def mark_reviewed(self, request, queryset):
        queryset.update(status="reviewed")

    @admin.action(description="Respinge raportul")
    def mark_dismissed(self, request, queryset):
        queryset.update(status="dismissed")

    @admin.action(description="Marchează cu acțiune aplicată")
    def mark_action_taken(self, request, queryset):
        queryset.update(status="action_taken")


@admin.register(UserStrike)
class UserStrikeAdmin(admin.ModelAdmin):
    list_display = ("user", "reason", "is_active", "created_by", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__username", "user__email", "reason", "notes")
    autocomplete_fields = ("user", "created_by")
