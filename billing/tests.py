import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from categories.models import Category
from listings.models import Listing

from .models import PaymentWebhookEvent, PromotionOrder, PromotionPlan

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

    def test_owner_cannot_promote_inactive_listing(self):
        self.listing.status = "inactive"
        self.listing.save(update_fields=["status", "updated_at"])

        self.client.login(username="owner", password="OwnerPass123!")
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

    def _signed_webhook_headers(self, body, secret="test-webhook-secret", timestamp=None):
        timestamp = str(timestamp or int(time.time()))
        signature = hmac.new(
            secret.encode("utf-8"),
            timestamp.encode("utf-8") + b"." + body,
            hashlib.sha256,
        ).hexdigest()
        return {
            "HTTP_X_MICU_TIMESTAMP": timestamp,
            "HTTP_X_MICU_SIGNATURE": f"sha256={signature}",
        }

    @override_settings(BILLING_WEBHOOK_SECRET="test-webhook-secret")
    def test_promotion_webhook_rejects_invalid_signature(self):
        order = PromotionOrder.objects.create(
            listing=self.listing,
            user=self.owner,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
        )
        body = json.dumps({"event_id": "evt_bad", "order_id": order.pk, "status": "paid"}).encode("utf-8")

        response = self.client.post(
            reverse("billing:promotion_webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_MICU_TIMESTAMP=str(int(time.time())),
            HTTP_X_MICU_SIGNATURE="sha256=wrong",
        )

        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(order.status, "pending")
        self.assertFalse(self.listing.is_promoted)

    @override_settings(BILLING_WEBHOOK_SECRET="test-webhook-secret")
    def test_signed_paid_webhook_applies_promotion(self):
        order = PromotionOrder.objects.create(
            listing=self.listing,
            user=self.owner,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
        )
        body = json.dumps(
            {
                "provider": "manual-test",
                "event_id": "evt_paid",
                "order_id": order.pk,
                "status": "paid",
                "external_reference": "pay_123",
            }
        ).encode("utf-8")

        response = self.client.post(
            reverse("billing:promotion_webhook"),
            data=body,
            content_type="application/json",
            **self._signed_webhook_headers(body),
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(order.status, "applied")
        self.assertEqual(order.external_reference, "pay_123")
        self.assertTrue(self.listing.is_promoted)
        self.assertEqual(PaymentWebhookEvent.objects.filter(event_id="evt_paid").count(), 1)

    @override_settings(BILLING_WEBHOOK_SECRET="test-webhook-secret")
    def test_duplicate_webhook_event_is_idempotent(self):
        order = PromotionOrder.objects.create(
            listing=self.listing,
            user=self.owner,
            plan=self.plan,
            amount=self.plan.price,
            currency=self.plan.currency,
        )
        body = json.dumps({"event_id": "evt_once", "order_id": order.pk, "status": "paid"}).encode("utf-8")
        headers = self._signed_webhook_headers(body)

        first = self.client.post(
            reverse("billing:promotion_webhook"),
            data=body,
            content_type="application/json",
            **headers,
        )
        self.listing.refresh_from_db()
        first_until = self.listing.featured_until

        second = self.client.post(
            reverse("billing:promotion_webhook"),
            data=body,
            content_type="application/json",
            **headers,
        )
        self.listing.refresh_from_db()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["duplicate"])
        self.assertEqual(self.listing.featured_until, first_until)
        self.assertEqual(PaymentWebhookEvent.objects.filter(event_id="evt_once").count(), 1)
