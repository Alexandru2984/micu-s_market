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
        # Categories are browsed through the filtered listings list (?category=slug);
        # the categories:category_detail route takes no slug, so reversing it raised
        # NoReverseMatch (500) wherever get_absolute_url was used.
        return f"{reverse('listings:list')}?category={self.slug}"

    @property
    def get_all_children(self):
        """Return all subcategories recursively (with infinite-loop protection)"""
        return self._collect_children(visited=set())

    def _collect_children(self, visited):
        """Recursive collection with a visited set to prevent infinite cycles"""
        children = []
        if self.pk in visited:
            return children  # prevents infinite recursion
        visited.add(self.pk)
        for child in self.subcategories.filter(is_active=True):
            children.append(child)
            children.extend(child._collect_children(visited))
        return children
