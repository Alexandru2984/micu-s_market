"""
Tests for the authentication and profiles system
"""
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image as PilImage

from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserReport

User = get_user_model()


def create_test_avatar(filename='avatar.jpg', size=(900, 900), color=(0, 128, 255)):
    buffer = BytesIO()
    image = PilImage.new('RGB', size, color)
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/jpeg')


class AuthViewsTestCase(TestCase):
    """Tests for login, logout, register"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_login_view_get(self):
        """The login page loads correctly"""
        response = self.client.get(reverse('accounts:login'))
        self.assertIn(response.status_code, [200, 301, 302])

    def test_login_authenticated_redirect(self):
        """An authenticated user is redirected away from login"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)

    def test_login_rejects_external_next_url(self):
        """Login does not redirect to external domains via next"""
        response = self.client.post(
            reverse('accounts:login') + '?next=https://evil.example/phish',
            {'username': 'testuser', 'password': 'SecurePass123!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('listings:home'))

    def test_logout_requires_post(self):
        """Custom logout accepts POST ONLY, not GET (CSRF force-logout protection)"""
        self.client.login(username='testuser', password='SecurePass123!')

        # A GET on logout must NOT log the user out
        response = self.client.get(reverse('accounts:logout'))
        # It must return 405 (Method Not Allowed)
        self.assertEqual(response.status_code, 405)

    def test_logout_post_works(self):
        """Logout via POST works correctly"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_register_view_get(self):
        """The registration page loads"""
        response = self.client.get(reverse('accounts:register'))
        self.assertIn(response.status_code, [200, 301, 302])

    def test_register_form_rejects_duplicate_email(self):
        form = CustomUserCreationForm(
            data={
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'TEST@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_profile_view_requires_login(self):
        """The profile view requires authentication"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_profile_view_authenticated(self):
        """The profile is shown for an authenticated user"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_form_rejects_another_users_email(self):
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!',
        )
        form = UserProfileForm(
            data={
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': 'OTHER@example.com',
                'bio': '',
                'phone': '',
                'city': '',
                'county': '',
                'date_of_birth': '',
            },
            instance=self.user.profile,
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_request_verification_requires_login(self):
        """The verification request requires authentication."""
        response = self.client.post(reverse('accounts:request_verification'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_request_verification(self):
        """An authenticated user can request profile verification."""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:request_verification'))

        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.verification_status, 'pending')
        self.assertIsNotNone(self.user.profile.verification_requested_at)

    def test_pending_verification_request_is_not_duplicated(self):
        """A pending request is not overwritten by repeated POSTs."""
        self.user.profile.request_verification()
        requested_at = self.user.profile.verification_requested_at

        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.post(reverse('accounts:request_verification'))

        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.verification_status, 'pending')
        self.assertEqual(self.user.profile.verification_requested_at, requested_at)

    def test_public_profile_view(self):
        """The public profile is accessible without authentication"""
        response = self.client.get(
            reverse('accounts:public_profile', kwargs={'username': self.user.username})
        )
        self.assertIn(response.status_code, [200, 404])  # 404 if no profile exists

    def test_report_user_requires_login(self):
        response = self.client.post(
            reverse('accounts:report_user', kwargs={'username': self.user.username}),
            {'reason': 'spam', 'details': 'test'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserReport.objects.exists())

    def test_user_can_report_another_user_once(self):
        User.objects.create_user(
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
    """Tests for the UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='profiletest',
            email='profile@example.com',
            password='TestPass123!'
        )

    def test_profile_created_on_user_creation(self):
        """The profile is created automatically when a user is created"""
        from accounts.models import UserProfile
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_update_statistics_no_reviews(self):
        """update_statistics works without any reviews"""
        profile = self.user.profile
        profile.update_statistics()
        self.assertEqual(profile.average_rating, 0)
        self.assertEqual(profile.total_listings, 0)

    def test_approve_verification_marks_profile_verified(self):
        """Approving verification sets the real badge."""
        profile = self.user.profile
        profile.request_verification()
        profile.approve_verification()

        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)
        self.assertEqual(profile.verification_status, 'verified')
        self.assertIsNotNone(profile.verification_reviewed_at)

    def test_reject_verification_marks_profile_rejected(self):
        """Rejecting verification keeps the profile unverified."""
        profile = self.user.profile
        profile.request_verification()
        profile.reject_verification('Date insuficiente.')

        profile.refresh_from_db()
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.verification_status, 'rejected')
        self.assertEqual(profile.verification_note, 'Date insuficiente.')

    @override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}})
    def test_avatar_resize_does_not_require_local_path(self):
        """Avatar optimization works with storages that do not expose .path."""
        profile = self.user.profile
        profile.avatar = create_test_avatar()
        profile.save()

        with profile.avatar.open('rb') as stored:
            optimized = PilImage.open(stored)
            self.assertLessEqual(optimized.width, 300)
            self.assertLessEqual(optimized.height, 300)
