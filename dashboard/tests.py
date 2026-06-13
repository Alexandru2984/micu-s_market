from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from categories.models import Category
from favorites.models import Favorite
from listings.models import Listing, ListingReport

User = get_user_model()


class SellerInsightsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="SellerPass123!",
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="BuyerPass123!",
        )
        self.other_seller = User.objects.create_user(
            username="other-seller",
            email="other-seller@example.com",
            password="OtherPass123!",
        )
        self.category = Category.objects.create(
            name="Dashboard Test",
            slug="dashboard-test",
            is_active=True,
        )
        self.listing = Listing.objects.create(
            title="Anunț performant",
            description="Test",
            price=100,
            owner=self.seller,
            category=self.category,
            city="Cluj",
            status="active",
            views_count=42,
            is_featured=True,
            featured_until=timezone.now() + timedelta(days=5),
        )
        Listing.objects.create(
            title="Anunț străin",
            description="Test",
            price=200,
            owner=self.other_seller,
            category=self.category,
            city="Iași",
            status="active",
            views_count=999,
        )

    def test_seller_insights_requires_login(self):
        response = self.client.get(reverse("dashboard:seller_insights"))
        self.assertEqual(response.status_code, 302)

    def test_seller_insights_shows_owner_stats_only(self):
        Favorite.objects.create(user=self.buyer, listing=self.listing)
        ListingReport.objects.create(
            listing=self.listing,
            reporter=self.buyer,
            reason="misleading",
        )

        self.client.login(username="seller", password="SellerPass123!")
        response = self.client.get(reverse("dashboard:seller_insights"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"]["total_listings"], 1)
        self.assertEqual(response.context["stats"]["total_views"], 42)
        self.assertEqual(response.context["stats"]["total_favorites"], 1)
        self.assertEqual(response.context["stats"]["active_promotions"], 1)
        self.assertEqual(list(response.context["top_listings"]), [self.listing])
        self.assertEqual(len(response.context["open_reports"]), 1)
