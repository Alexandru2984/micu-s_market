"""
Teste pentru sistemul de autentificare și profiluri
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserReport

User = get_user_model()


class AuthViewsTestCase(TestCase):
    """Teste pentru login, logout, register"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_login_view_get(self):
        """Pagina de login se încarcă corect"""
        response = self.client.get(reverse('accounts:login'))
        self.assertIn(response.status_code, [200, 301, 302])

    def test_login_authenticated_redirect(self):
        """Utilizatorul autentificat este redirecționat de pe login"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)

    def test_login_rejects_external_next_url(self):
        """Loginul nu redirecționează către domenii externe din next"""
        response = self.client.post(
            reverse('accounts:login') + '?next=https://evil.example/phish',
            {'username': 'testuser', 'password': 'SecurePass123!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('listings:home'))

    def test_logout_requires_post(self):
        """Logout custom acceptă DOAR POST, nu GET (protecție CSRF force-logout)"""
        self.client.login(username='testuser', password='SecurePass123!')
        
        # GET pe logout NU trebuie să deconecteze
        response = self.client.get(reverse('accounts:logout'))
        # Trebuie să returneze 405 (Method Not Allowed)
        self.assertEqual(response.status_code, 405)

    def test_logout_post_works(self):
        """Logout via POST funcționează corect"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_register_view_get(self):
        """Pagina de înregistrare se încarcă"""
        response = self.client.get(reverse('accounts:register'))
        self.assertIn(response.status_code, [200, 301, 302])

    def test_profile_view_requires_login(self):
        """Profile view necesită autentificare"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_profile_view_authenticated(self):
        """Profilul se afișează pentru utilizatorul autentificat"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_request_verification_requires_login(self):
        """Cererea de verificare necesită autentificare."""
        response = self.client.post(reverse('accounts:request_verification'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_request_verification(self):
        """Utilizatorul autentificat poate cere verificarea profilului."""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:request_verification'))

        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.verification_status, 'pending')
        self.assertIsNotNone(self.user.profile.verification_requested_at)

    def test_pending_verification_request_is_not_duplicated(self):
        """Cererea pending nu este rescrisă la POST-uri repetate."""
        self.user.profile.request_verification()
        requested_at = self.user.profile.verification_requested_at

        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:request_verification'))

        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.verification_status, 'pending')
        self.assertEqual(self.user.profile.verification_requested_at, requested_at)

    def test_public_profile_view(self):
        """Profilul public este accesibil fără autentificare"""
        response = self.client.get(
            reverse('accounts:public_profile', kwargs={'username': self.user.username})
        )
        self.assertIn(response.status_code, [200, 404])  # 404 dacă nu există profil

    def test_report_user_requires_login(self):
        response = self.client.post(
            reverse('accounts:report_user', kwargs={'username': self.user.username}),
            {'reason': 'spam', 'details': 'test'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserReport.objects.exists())

    def test_user_can_report_another_user_once(self):
        reporter = User.objects.create_user(
            username='reporter',
            email='reporter@example.com',
            password='ReporterPass123!',
        )
        self.client.login(username='reporter', password='ReporterPass123!')
        response = self.client.post(
            reverse('accounts:report_user', kwargs={'username': self.user.username}),
            {'reason': 'spam', 'details': 'Trimite spam.'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserReport.objects.count(), 1)

        response = self.client.post(
            reverse('accounts:report_user', kwargs={'username': self.user.username}),
            {'reason': 'fake_profile', 'details': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserReport.objects.count(), 1)


class UserProfileModelTestCase(TestCase):
    """Teste pentru modelul UserProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='profiletest',
            email='profile@example.com',
            password='TestPass123!'
        )

    def test_profile_created_on_user_creation(self):
        """Profilul este creat automat când se creează un user"""
        from accounts.models import UserProfile
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_update_statistics_no_reviews(self):
        """update_statistics funcționează fără review-uri"""
        profile = self.user.profile
        profile.update_statistics()
        self.assertEqual(profile.average_rating, 0)
        self.assertEqual(profile.total_listings, 0)

    def test_approve_verification_marks_profile_verified(self):
        """Aprobarea verificării setează badge-ul real."""
        profile = self.user.profile
        profile.request_verification()
        profile.approve_verification()

        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)
        self.assertEqual(profile.verification_status, 'verified')
        self.assertIsNotNone(profile.verification_reviewed_at)

    def test_reject_verification_marks_profile_rejected(self):
        """Respingerea verificării păstrează profilul neverificat."""
        profile = self.user.profile
        profile.request_verification()
        profile.reject_verification('Date insuficiente.')

        profile.refresh_from_db()
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.verification_status, 'rejected')
        self.assertEqual(profile.verification_note, 'Date insuficiente.')
