from django.contrib import admin
from .models import Favorite, SavedSearch

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'created_at']
    list_filter = ['created_at', 'listing__category']
    search_fields = ['user__username', 'listing__title']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'listing')

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'search_query', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'category']
    search_fields = ['user__username', 'name', 'search_query']
    readonly_fields = ['created_at']
