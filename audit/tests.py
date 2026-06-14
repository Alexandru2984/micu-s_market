from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from .models import AuditEvent
from categories.models import Category
from listings.admin import ListingAdmin
from listings.models import Listing

User = get_user_model()


class ObservabilityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="audit-user",
            email="audit@example.com",
            password="AuditPass123!",
        )

    def test_request_id_header_is_returned(self):
        response = self.client.get(reverse("healthcheck"), HTTP_X_REQUEST_ID="test-request-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Request-ID"], "test-request-id")

    def test_login_creates_audit_event(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "audit-user", "password": "AuditPass123!"},
            HTTP_X_REQUEST_ID="login-request",
        )

        self.assertEqual(response.status_code, 302)
        event = AuditEvent.objects.get(event_type="auth.login")
        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.request_id, "login-request")

    def test_listing_admin_moderation_action_creates_audit_event(self):
        category = Category.objects.create(name="Audit", slug="audit", is_active=True)
        listing = Listing.objects.create(
            title="Audit listing",
            description="Test",
            price=10,
            owner=self.user,
            category=category,
            city="Iasi",
            status="inactive",
            needs_moderation_review=True,
            risk_score=80,
        )
        admin_user = User.objects.create_superuser(
            username="audit-admin",
            email="audit-admin@example.com",
            password="AdminPass123!",
        )
        request = RequestFactory().post("/admin/listings/listing/")
        request.user = admin_user
        request.request_id = "admin-action-request"

        ListingAdmin(Listing, AdminSite()).approve_moderation(request, Listing.objects.filter(pk=listing.pk))

        event = AuditEvent.objects.get(event_type="listing.moderation_approved")
        self.assertEqual(event.actor, admin_user)
        self.assertEqual(event.object_type, "Listing")
        self.assertEqual(event.object_id, str(listing.pk))
        self.assertEqual(event.request_id, "admin-action-request")

    @override_settings(TRUSTED_PROXY_CHAIN_CONFIGURED=False)
    def test_audit_log_ignores_forwarded_for_without_trusted_proxy(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "audit-user", "password": "AuditPass123!"},
            REMOTE_ADDR="198.51.100.10",
            HTTP_X_FORWARDED_FOR="203.0.113.99",
        )

        self.assertEqual(response.status_code, 302)
        event = AuditEvent.objects.get(event_type="auth.login")
        self.assertEqual(str(event.ip_address), "198.51.100.10")

    @override_settings(TRUSTED_PROXY_CHAIN_CONFIGURED=True)
    def test_audit_log_uses_forwarded_for_with_trusted_proxy(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "audit-user", "password": "AuditPass123!"},
            REMOTE_ADDR="198.51.100.10",
            HTTP_X_FORWARDED_FOR="203.0.113.99",
        )

        self.assertEqual(response.status_code, 302)
        event = AuditEvent.objects.get(event_type="auth.login")
        self.assertEqual(str(event.ip_address), "203.0.113.99")
