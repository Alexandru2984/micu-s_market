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
