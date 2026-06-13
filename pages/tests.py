from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .views import bad_request_view, permission_denied_view, server_error_view


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

    def test_manifest_endpoint_returns_pwa_metadata(self):
        response = self.client.get(reverse('manifest'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/manifest+json')
        self.assertEqual(response.json()['short_name'], 'Micu Market')

    def test_service_worker_endpoint_is_root_scoped(self):
        response = self.client.get(reverse('service_worker'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/javascript', response['Content-Type'])
        self.assertContains(response, 'self.addEventListener("fetch"', status_code=200)

    def test_offline_page_is_noindex(self):
        response = self.client.get(reverse('offline'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex,nofollow">')

    def test_home_links_manifest_and_pwa_registration(self):
        response = self.client.get(reverse('listings:home'))

        self.assertContains(response, '<link rel="manifest" href="/manifest.webmanifest">')
        self.assertContains(response, '/static/js/pwa.js')

    def test_home_includes_cookie_consent(self):
        response = self.client.get(reverse('listings:home'))

        self.assertContains(response, 'id="cookieConsent"')
        self.assertContains(response, reverse('pages:privacy'))
        self.assertContains(response, '/static/js/cookie-consent.js')

    def test_privacy_page_documents_cookie_policy(self):
        response = self.client.get(reverse('pages:privacy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Politica de confidențialitate')
        self.assertContains(response, 'Cookie-uri')

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_custom_404_page_is_rendered(self):
        response = self.client.get('/pagina-care-nu-exista/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Pagina nu există', status_code=404)
        self.assertContains(response, 'noindex,nofollow', status_code=404)

    def test_custom_error_views_render_noindex_pages(self):
        request = RequestFactory().get('/error-test/')

        response_400 = bad_request_view(request, Exception('bad request'))
        response_403 = permission_denied_view(request, Exception('denied'))
        response_500 = server_error_view(request)

        self.assertEqual(response_400.status_code, 400)
        self.assertContains(response_400, 'Cerere invalidă', status_code=400)
        self.assertContains(response_403, 'Acces restricționat', status_code=403)
        self.assertContains(response_500, 'Eroare server', status_code=500)


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
