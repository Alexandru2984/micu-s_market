from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from categories.models import Category
from listings.models import Listing

from .models import PromotionOrder, PromotionPlan

User = get_user_model()


class PromotionOrderTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="OwnerPass123!",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="OtherPass123!",
        )
        self.category = Category.objects.create(name="Billing", slug="billing", is_active=True)
        self.listing = Listing.objects.create(
            title="Anunț de promovat",
            description="Test",
            price=100,
            owner=self.owner,
            category=self.category,
            city="București",
            status="active",
        )
        self.plan = PromotionPlan.objects.create(name="Start", days=7, price=19)

    def test_owner_can_create_promotion_order(self):
        self.client.login(username="owner", password="OwnerPass123!")
        response = self.client.post(
            reverse("billing:promote_listing", kwargs={"slug": self.listing.slug}),
            {"plan": self.plan.pk},
        )

        self.assertEqual(response.status_code, 302)
        order = PromotionOrder.objects.get()
        self.assertEqual(order.listing, self.listing)
        self.assertEqual(order.amount, self.plan.price)

    def test_non_owner_cannot_promote_listing(self):
        self.client.login(username="other", password="OtherPass123!")
        response = self.client.post(
            reverse("billing:promote_listing", kwargs={"slug": self.listing.slug}),
            {"plan": self.plan.pk},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(PromotionOrder.objects.exists())

    def test_pending_order_cannot_apply_promotion(self):
        order = PromotionOrder.objects.create(
            listing=self.listing,
            user=self.owner,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
        )

        self.assertFalse(order.apply_promotion())
        self.listing.refresh_from_db()
        order.refresh_from_db()
        self.assertFalse(self.listing.is_promoted)
        self.assertEqual(order.status, "pending")

    def test_apply_promotion_updates_paid_listing(self):
        order = PromotionOrder.objects.create(
            listing=self.listing,
            user=self.owner,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
        )
        order.mark_paid()

        self.assertTrue(order.apply_promotion())
        self.listing.refresh_from_db()
        order.refresh_from_db()
        self.assertTrue(self.listing.is_promoted)
        self.assertEqual(order.status, "applied")
        self.assertIsNotNone(order.paid_at)
