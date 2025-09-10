from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Order for display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categorii'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('categories:category_detail', kwargs={'slug': self.slug})
    
    @property
    def get_all_children(self):
        """Returnează toate subcategoriile recursiv"""
        children = list(self.subcategories.filter(is_active=True))
        for child in self.subcategories.filter(is_active=True):
            children.extend(child.get_all_children)
        return children
