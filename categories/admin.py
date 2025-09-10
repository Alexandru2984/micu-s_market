from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'este_activa', 'order', 'data_creare')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order',)
    
    fieldsets = (
        ('Informații de bază', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Organizare', {
            'fields': ('parent', 'order', 'is_active')
        }),
    )
    
    def este_activa(self, obj):
        return obj.is_active
    este_activa.short_description = 'Activă'
    este_activa.boolean = True
    
    def data_creare(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    data_creare.short_description = 'Data creării'
