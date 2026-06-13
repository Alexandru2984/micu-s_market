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
