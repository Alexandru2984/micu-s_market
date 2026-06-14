"""
Teste pentru anunțuri — CRUD, access control, validare imagini
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.cache import cache
from django.utils import timezone
from io import BytesIO
from pathlib import Path
from io import StringIO
import tempfile
from datetime import timedelta
from PIL import Image as PilImage

from .models import Listing, ListingReport
from categories.models import Category
from notifications.models import Notification

User = get_user_model()


def create_test_image(filename='test.jpg', size=(100, 100), color=(255, 0, 0)):
    """Generează un fișier imagine valid pentru teste"""
    buffer = BytesIO()
    img = PilImage.new('RGB', size, color)
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/jpeg')


class ListingCRUDTestCase(TestCase):
    """Teste pentru crearea, editarea, ștergerea anunțurilor"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='SellerPass123!'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='OtherPass123!'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        self.listing = Listing.objects.create(
            title='Anunț test',
            description='Descriere test',
            price=100.00,
            owner=self.user,
            category=self.category,
            city='București',
            status='active'
        )

    def test_listing_create_requires_login(self):
        """Crearea de anunțuri necesită autentificare"""
        response = self.client.get(reverse('listings:create'))
        self.assertEqual(response.status_code, 302)

    def test_listing_create_authenticated(self):
        """Utilizatorul autentificat poate accesa formularul de creare"""
        self.client.login(username='seller', password='SellerPass123!')
        response = self.client.get(reverse('listings:create'))
        self.assertEqual(response.status_code, 200)

    def test_listing_detail_accessible(self):
        """Detaliile unui anunț activ sunt accesibile fără autentificare"""
        response = self.client.get(
            reverse('listings:detail', kwargs={'slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_listing_detail_view_count_has_cooldown(self):
        """Refreshurile repetate de la același client nu scriu view-uri nelimitat."""
        cache.clear()
        url = reverse('listings:detail', kwargs={'slug': self.listing.slug})

        self.client.get(url, HTTP_USER_AGENT='test-agent', REMOTE_ADDR='127.0.0.1')
        self.client.get(url, HTTP_USER_AGENT='test-agent', REMOTE_ADDR='127.0.0.1')

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views_count, 1)

    def test_listing_detail_has_seo_metadata(self):
        """Pagina de anunț expune meta tags și structured data pentru indexare/share."""
        response = self.client.get(
            reverse('listings:detail', kwargs={'slug': self.listing.slug})
        )

        self.assertContains(response, '<meta property="og:type" content="product">')
        self.assertContains(response, '<script type="application/ld+json">')
        self.assertContains(response, '"@type": "Product"')
        self.assertContains(response, f'<link rel="canonical" href="http://testserver{self.listing.get_absolute_url()}">')

    def test_listing_edit_requires_owner(self):
        """Editarea anunțului este permisă doar proprietarului"""
        self.client.login(username='other', password='OtherPass123!')
        response = self.client.get(
            reverse('listings:update', kwargs={'slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_listing_delete_requires_owner(self):
        """Ștergerea anunțului este permisă doar proprietarului"""
        self.client.login(username='other', password='OtherPass123!')
        response = self.client.post(
            reverse('listings:delete', kwargs={'slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 404)
        # Anunțul NU trebuie șters
        self.assertTrue(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_listing_owner_can_delete(self):
        """Proprietarul poate șterge propriul anunț"""
        self.client.login(username='seller', password='SellerPass123!')
        response = self.client.post(
            reverse('listings:delete', kwargs={'slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_slug_generated_on_create(self):
        """Slug-ul este generat automat la crearea anunțului"""
        self.assertIsNotNone(self.listing.slug)
        self.assertIn('anunt', self.listing.slug.lower())

    def test_pages_home_view_filters_active(self):
        """pages/home_view returnează doar anunțuri active"""
        # Creează un anunț inactiv
        inactive = Listing.objects.create(
            title='Anunț inactiv',
            description='Test',
            price=50.00,
            owner=self.user,
            category=self.category,
            city='Cluj',
            status='inactive'
        )
        response = self.client.get(reverse('listings:home'))  # listings:home
        # Anunțul inactiv nu trebuie să apară în response
        if response.status_code == 200:
            self.assertNotIn(b'Anun\xc8\x9b inactiv', response.content)

    def test_report_listing_requires_login(self):
        """Raportarea unui anunț necesită autentificare."""
        response = self.client.post(
            reverse('listings:report', kwargs={'slug': self.listing.slug}),
            {'reason': 'scam', 'details': 'suspect'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ListingReport.objects.exists())

    def test_owner_cannot_report_own_listing(self):
        """Proprietarul nu își poate raporta propriul anunț."""
        self.client.login(username='seller', password='SellerPass123!')
        response = self.client.post(
            reverse('listings:report', kwargs={'slug': self.listing.slug}),
            {'reason': 'scam', 'details': 'suspect'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ListingReport.objects.exists())

    def test_authenticated_user_can_report_listing(self):
        """Un utilizator autentificat poate raporta un anunț străin."""
        self.client.login(username='other', password='OtherPass123!')
        response = self.client.post(
            reverse('listings:report', kwargs={'slug': self.listing.slug}),
            {'reason': 'misleading', 'details': 'Prețul pare fals.'},
        )
        self.assertEqual(response.status_code, 302)
        report = ListingReport.objects.get()
        self.assertEqual(report.listing, self.listing)
        self.assertEqual(report.reporter, self.other_user)
        self.assertEqual(report.reason, 'misleading')

    def test_duplicate_active_report_is_prevented(self):
        """Utilizatorul nu poate crea două rapoarte active pentru același anunț."""
        ListingReport.objects.create(
            listing=self.listing,
            reporter=self.other_user,
            reason='scam',
        )
        self.client.login(username='other', password='OtherPass123!')
        response = self.client.post(
            reverse('listings:report', kwargs={'slug': self.listing.slug}),
            {'reason': 'duplicate', 'details': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ListingReport.objects.count(), 1)

    @override_settings(LISTING_AUTO_HIDE_REPORT_THRESHOLD=2)
    def test_listing_auto_hides_after_report_threshold(self):
        """Anunțul este ascuns temporar după pragul de rapoarte active."""
        reporter_one = User.objects.create_user(
            username='reporter1',
            email='reporter1@example.com',
            password='ReporterPass123!',
        )
        ListingReport.objects.create(
            listing=self.listing,
            reporter=reporter_one,
            reason='scam',
        )

        self.client.login(username='other', password='OtherPass123!')
        response = self.client.post(
            reverse('listings:report', kwargs={'slug': self.listing.slug}),
            {'reason': 'misleading', 'details': ''},
        )

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, 'inactive')
        self.assertTrue(Notification.objects.filter(recipient=self.user, notification_type='listing_rejected').exists())

    def test_promoted_listing_property_respects_expiry(self):
        """Promovarea este activă doar cât timp nu a expirat."""
        self.listing.is_featured = True
        self.listing.featured_until = timezone.now() + timedelta(days=1)
        self.assertTrue(self.listing.is_promoted)

        self.listing.featured_until = timezone.now() - timedelta(minutes=1)
        self.assertFalse(self.listing.is_promoted)

    def test_home_shows_only_active_promoted_listings(self):
        """Homepage afișează doar promovările active în secțiunea recomandată."""
        active_promoted = Listing.objects.create(
            title='Promovat activ',
            description='Test',
            price=120.00,
            owner=self.user,
            category=self.category,
            city='Iași',
            status='active',
            is_featured=True,
            featured_until=timezone.now() + timedelta(days=3),
        )
        expired_promoted = Listing.objects.create(
            title='Promovat expirat',
            description='Test',
            price=130.00,
            owner=self.user,
            category=self.category,
            city='Iași',
            status='active',
            is_featured=True,
            featured_until=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(reverse('listings:home'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(active_promoted, response.context['featured_listings'])
        self.assertNotIn(expired_promoted, response.context['featured_listings'])

    @override_settings(LISTING_RISK_REVIEW_THRESHOLD=70)
    def test_suspicious_listing_is_sent_to_moderation_on_create(self):
        """Anunțurile cu risc mare sunt ascunse temporar pentru review."""
        self.client.login(username='seller', password='SellerPass123!')

        response = self.client.post(
            reverse('listings:create'),
            {
                'title': 'Telefon urgent whatsapp',
                'description': 'Plata in avans prin western union. Scrie pe whatsapp.',
                'category': self.category.id,
                'price': '1.00',
                'city': 'București',
                'county': 'București',
                'condition': 'good',
                'negotiable': 'on',
            },
        )

        listing = Listing.objects.get(title='Telefon urgent whatsapp')
        self.assertRedirects(response, reverse('listings:my_listings'))
        self.assertEqual(listing.status, 'inactive')
        self.assertTrue(listing.needs_moderation_review)
        self.assertGreaterEqual(listing.risk_score, 70)
        self.assertIn('Termeni sensibili', listing.moderation_note)
        self.assertTrue(Notification.objects.filter(recipient=self.user, notification_type='listing_rejected').exists())

    @override_settings(LISTING_RISK_REVIEW_THRESHOLD=70)
    def test_normal_listing_remains_public_on_create(self):
        """Anunțurile normale rămân active după creare."""
        self.client.login(username='seller', password='SellerPass123!')

        response = self.client.post(
            reverse('listings:create'),
            {
                'title': 'Scaun birou ergonomic',
                'description': 'Scaun reglabil, stare bună, disponibil pentru ridicare locală.',
                'category': self.category.id,
                'price': '250.00',
                'city': 'București',
                'county': 'București',
                'condition': 'good',
                'negotiable': 'on',
            },
        )

        listing = Listing.objects.get(title='Scaun birou ergonomic')
        self.assertRedirects(response, reverse('listings:detail', kwargs={'slug': listing.slug}))
        self.assertEqual(listing.status, 'active')
        self.assertFalse(listing.needs_moderation_review)

    def test_category_icon_is_escaped_in_listing_filter(self):
        """Iconul categoriei nu este randat ca HTML raw în filtrul de listare."""
        self.category.icon = '<script>alert(1)</script>'
        self.category.save(update_fields=['icon'])

        response = self.client.get(reverse('listings:list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script>alert(1)</script>', html=False)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')


class ListingImageValidationTestCase(TestCase):
    """Teste pentru validarea imaginilor uploadate"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='imgtest',
            email='img@example.com',
            password='ImgPass123!'
        )
        self.client.login(username='imgtest', password='ImgPass123!')

    def test_valid_image_passes(self):
        """O imagine JPEG validă trece validarea"""
        from listings.forms import ListingImageForm
        img_file = create_test_image()
        form = ListingImageForm(files={'image': img_file})
        self.assertTrue(form.is_valid(), form.errors)

    def test_oversized_image_rejected(self):
        """O imagine mai mare de 5MB este respinsă"""
        from listings.forms import ListingImageForm
        # Creează un fișier fals de 6MB
        big_file = SimpleUploadedFile('big.jpg', b'0' * (6 * 1024 * 1024), content_type='image/jpeg')
        form = ListingImageForm(files={'image': big_file})
        self.assertFalse(form.is_valid())

    def test_wrong_extension_rejected(self):
        """Un fișier cu extensie nepermisă este respins"""
        from listings.forms import ListingImageForm
        fake_file = SimpleUploadedFile('malware.exe', b'MZ...fake', content_type='application/octet-stream')
        form = ListingImageForm(files={'image': fake_file})
        self.assertFalse(form.is_valid())


class MediaCleanupCommandTestCase(TestCase):
    def test_cleanup_orphan_media_reports_files_without_deleting_by_default(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                orphan = Path(media_root) / "orphans" / "old.txt"
                orphan.parent.mkdir(parents=True)
                orphan.write_text("orphan", encoding="utf-8")

                output = StringIO()
                call_command("cleanup_orphan_media", stdout=output)

                self.assertIn("orphans/old.txt", output.getvalue())
                self.assertTrue(orphan.exists())
