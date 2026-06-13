from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase
from django.urls import reverse


class ProjectUrlSecurityTests(TestCase):
    def test_admin_url_is_not_default_admin_path(self):
        self.assertNotEqual(reverse('admin:index'), '/admin/')

    def test_healthcheck_returns_ok(self):
        response = self.client.get(reverse('pages:healthcheck'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.json()['database'], 'ok')

    def test_root_healthcheck_returns_ok(self):
        response = self.client.get(reverse('healthcheck'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_security_headers_are_present(self):
        response = self.client.get(reverse('healthcheck'))
        self.assertEqual(response['Permissions-Policy'], 'geolocation=(), microphone=(), camera=()')
        self.assertEqual(response['X-Permitted-Cross-Domain-Policies'], 'none')
        self.assertEqual(response['Cross-Origin-Resource-Policy'], 'same-site')


class DoctorCommandTests(TestCase):
    def test_doctor_checks_core_services(self):
        out = StringIO()

        call_command("doctor", stdout=out)

        output = out.getvalue()
        self.assertIn("OK database", output)
        self.assertIn("OK cache", output)
        self.assertIn("OK email", output)
        self.assertIn("OK storage", output)
        self.assertIn("Doctor checks passed.", output)

    @patch("pages.management.commands.doctor.cache.get", return_value="bad")
    def test_doctor_fails_when_cache_roundtrip_fails(self, _cache_get):
        with self.assertRaises(CommandError):
            call_command("doctor", "--skip-email", "--skip-storage", stdout=StringIO(), stderr=StringIO())
