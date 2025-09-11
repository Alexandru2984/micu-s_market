from django.contrib import admin
from .models import Review, ReviewResponse

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed_user', 'rating', 'transaction_type', 'listing', 'is_approved', 'created_at')
    list_filter = ('rating', 'transaction_type', 'is_approved', 'created_at')
    search_fields = ('reviewer__username', 'reviewed_user__username', 'title', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informații generale', {
            'fields': ('reviewer', 'reviewed_user', 'listing')
        }),
        ('Review', {
            'fields': ('rating', 'title', 'comment', 'transaction_type')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('reviewer', 'reviewed_user', 'listing')

@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('review', 'get_reviewer', 'get_reviewed_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('review__reviewer__username', 'review__reviewed_user__username', 'response_text')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Review asociat', {
            'fields': ('review',)
        }),
        ('Răspuns', {
            'fields': ('response_text',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_reviewer(self, obj):
        return obj.review.reviewer.username
    get_reviewer.short_description = 'Reviewer'
    get_reviewer.admin_order_field = 'review__reviewer__username'
    
    def get_reviewed_user(self, obj):
        return obj.review.reviewed_user.username
    get_reviewed_user.short_description = 'Utilizator evaluat'
    get_reviewed_user.admin_order_field = 'review__reviewed_user__username'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('review__reviewer', 'review__reviewed_user')
