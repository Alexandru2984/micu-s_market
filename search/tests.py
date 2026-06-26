from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from categories.models import Category
from favorites.models import SavedSearch

User = get_user_model()


class SavedSearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="searcher",
            email="searcher@example.com",
            password="SearchPass123!",
        )
        self.other = User.objects.create_user(
            username="other-searcher",
            email="other-searcher@example.com",
            password="OtherSearchPass123!",
        )
        self.category = Category.objects.create(name="Laptopuri", slug="laptopuri", is_active=True)

    def test_saved_searches_require_login(self):
        response = self.client.get(reverse("search:saved_searches"))

        self.assertEqual(response.status_code, 302)

    def test_user_can_create_saved_search(self):
        self.client.login(username="searcher", password="SearchPass123!")
        response = self.client.post(
            reverse("search:saved_searches"),
            {
                "name": "Laptop Cluj",
                "search_query": "thinkpad",
                "category": self.category.pk,
                "min_price": "1000",
                "max_price": "5000",
                "city": "Cluj",
                "county": "",
                "email_notifications": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        saved = SavedSearch.objects.get(user=self.user)
        self.assertEqual(saved.name, "Laptop Cluj")
        self.assertEqual(saved.search_query, "thinkpad")
        self.assertEqual(saved.category, self.category)

    def test_saved_search_rejects_empty_filters(self):
        self.client.login(username="searcher", password="SearchPass123!")
        response = self.client.post(
            reverse("search:saved_searches"),
            {"name": "Gol", "search_query": "", "city": "", "county": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SavedSearch.objects.exists())

    def test_run_saved_search_redirects_to_listing_filters(self):
        saved = SavedSearch.objects.create(
            user=self.user,
            name="Laptop Cluj",
            search_query="thinkpad",
            category=self.category,
            min_price=1000,
            city="Cluj",
        )
        self.client.login(username="searcher", password="SearchPass123!")

        response = self.client.get(reverse("search:run_saved_search", kwargs={"pk": saved.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("listings:list"), response.url)
        self.assertIn("search=thinkpad", response.url)
        self.assertIn("category=laptopuri", response.url)
        self.assertIn("city=Cluj", response.url)

    def test_user_cannot_delete_another_users_saved_search(self):
        saved = SavedSearch.objects.create(user=self.other, name="Altul", search_query="telefon")
        self.client.login(username="searcher", password="SearchPass123!")

        response = self.client.post(reverse("search:delete_saved_search", kwargs={"pk": saved.pk}))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(SavedSearch.objects.filter(pk=saved.pk).exists())
