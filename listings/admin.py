from django.contrib import admin
from .models import Listing, ListingImage, ListingReport

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image', 'alt_text', 'order')
    verbose_name = 'Imagine'
    verbose_name_plural = 'Imagini'

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "status_display", "este_activ", "oras", "data_creare")
    list_filter = ("status", "created_at", "category", "condition", "city")
    search_fields = ("title", "description", "city")
    readonly_fields = ("slug", "views_count", "created_at", "updated_at")
    inlines = [ListingImageInline]
    
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
            'fields': ('status', 'is_featured', 'expires_at')
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
    
    def oras(self, obj):
        return f"{obj.city}, {obj.county}"
    oras.short_description = 'Locație'
    
    def data_creare(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    data_creare.short_description = 'Creat la'


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
