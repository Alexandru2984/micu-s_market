from django.test import TestCase
from django.urls import reverse

from .models import Category


class CategoryUrlTests(TestCase):
    def test_get_absolute_url_points_to_listing_filter(self):
        """get_absolute_url must point to the filtered list, not a nonexistent route."""
        category = Category.objects.create(name="Electronice", slug="electronice", is_active=True)
        url = category.get_absolute_url()
        self.assertEqual(url, f"{reverse('listings:list')}?category=electronice")

    def test_home_page_with_categories_renders(self):
        """The page that lists categories no longer 500s (get_absolute_url regression)."""
        Category.objects.create(name="Auto", slug="auto", is_active=True, parent=None)
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
