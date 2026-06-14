from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Listing, ListingImage, ListingReport
from audit.utils import audit_log

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image', 'alt_text', 'order')
    verbose_name = 'Imagine'
    verbose_name_plural = 'Imagini'

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "status_display", "este_activ", "este_promovat", "needs_moderation_review", "risk_score", "oras", "data_creare")
    list_filter = ("status", "needs_moderation_review", "is_featured", "featured_until", "created_at", "category", "condition", "city")
    search_fields = ("title", "description", "city")
    readonly_fields = ("slug", "views_count", "risk_score", "moderation_note", "created_at", "updated_at")
    inlines = [ListingImageInline]
    actions = ("approve_moderation", "send_to_moderation", "promote_7_days", "promote_30_days", "stop_promotion")
    
    fieldsets = (
        ('Informații de bază', {
            'fields': ('title', 'description', 'price', 'negotiable')
        }),
        ('Categorie și stare', {
            'fields': ('category', 'condition')
        }),
        ('Locație', {
            'fields': ('city', 'county')
        }),
        ('Setări avansate', {
            'fields': ('status', 'is_featured', 'featured_until', 'expires_at')
        }),
        ('Moderare', {
            'fields': ('needs_moderation_review', 'risk_score', 'moderation_note')
        }),
        ('Informații sistem', {
            'fields': ('slug', 'views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status_mapping = {
            'active': 'Activ',
            'sold': 'Vândut', 
            'reserved': 'Rezervat',
            'inactive': 'Inactiv'
        }
        return status_mapping.get(obj.status, obj.status)
    status_display.short_description = 'Status'
    
    def este_activ(self, obj):
        return obj.is_active
    este_activ.short_description = 'Activ'
    este_activ.boolean = True

    def este_promovat(self, obj):
        return obj.is_promoted
    este_promovat.short_description = 'Promovat'
    este_promovat.boolean = True
    
    def oras(self, obj):
        return f"{obj.city}, {obj.county}"
    oras.short_description = 'Locație'
    
    def data_creare(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    data_creare.short_description = 'Creat la'

    @admin.action(description="Promovează 7 zile")
    def promote_7_days(self, request, queryset):
        featured_until = timezone.now() + timedelta(days=7)
        queryset.update(is_featured=True, featured_until=featured_until)
        for listing in queryset:
            audit_log("listing.promotion_started", request=request, obj=listing, metadata={"days": 7})

    @admin.action(description="Promovează 30 zile")
    def promote_30_days(self, request, queryset):
        featured_until = timezone.now() + timedelta(days=30)
        queryset.update(is_featured=True, featured_until=featured_until)
        for listing in queryset:
            audit_log("listing.promotion_started", request=request, obj=listing, metadata={"days": 30})

    @admin.action(description="Oprește promovarea")
    def stop_promotion(self, request, queryset):
        queryset.update(is_featured=False, featured_until=None)
        for listing in queryset:
            audit_log("listing.promotion_stopped", request=request, obj=listing)

    @admin.action(description="Aprobă moderarea și activează")
    def approve_moderation(self, request, queryset):
        queryset.update(needs_moderation_review=False, risk_score=0, moderation_note="", status="active")
        for listing in queryset:
            audit_log("listing.moderation_approved", request=request, obj=listing)

    @admin.action(description="Trimite la moderare")
    def send_to_moderation(self, request, queryset):
        queryset.update(needs_moderation_review=True, status="inactive")
        for listing in queryset:
            audit_log("listing.moderation_requested", request=request, obj=listing)


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = (
        "listing",
        "reporter",
        "reason",
        "status",
        "created_at",
    )
    list_filter = ("status", "reason", "created_at")
    search_fields = (
        "listing__title",
        "reporter__username",
        "reporter__email",
        "details",
        "moderator_note",
    )
    readonly_fields = ("listing", "reporter", "reason", "details", "created_at", "updated_at")
    actions = ("mark_reviewed", "mark_dismissed", "mark_action_taken")
    autocomplete_fields = ("listing", "reporter")

    fieldsets = (
        ("Raport", {
            "fields": ("listing", "reporter", "reason", "details"),
        }),
        ("Moderare", {
            "fields": ("status", "moderator_note"),
        }),
        ("Sistem", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.action(description="Marchează ca verificat")
    def mark_reviewed(self, request, queryset):
        queryset.update(status="reviewed")

    @admin.action(description="Respinge raportul")
    def mark_dismissed(self, request, queryset):
        queryset.update(status="dismissed")

    @admin.action(description="Marchează cu acțiune aplicată")
    def mark_action_taken(self, request, queryset):
        queryset.update(status="action_taken")

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ("anunt", "ordine", "data_creare")
    list_filter = ("created_at",)
    search_fields = ("listing__title", "alt_text")
    
    def anunt(self, obj):
        return obj.listing.title
    anunt.short_description = 'Anunț'
    
    def ordine(self, obj):
        return obj.order
    ordine.short_description = 'Ordine'
    
    def data_creare(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    data_creare.short_description = 'Creat la'
