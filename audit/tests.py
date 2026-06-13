from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import AuditEvent

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
