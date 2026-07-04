from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from categories.models import Category
from listings.models import Listing

from .models import Favorite, SavedSearch

User = get_user_model()


class FavoriteSecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='favorite-user',
            email='favorite@example.com',
            password='FavoritePass123!',
        )
        self.owner = User.objects.create_user(
            username='listing-owner',
            email='owner@example.com',
            password='OwnerPass123!',
        )
        self.category = Category.objects.create(
            name='Favorite Test Cat',
            slug='favorite-test-cat',
            is_active=True,
        )
        self.listing = Listing.objects.create(
            title='Produs favorit',
            description='Test',
            price=100,
            owner=self.owner,
            category=self.category,
            city='Cluj',
            status='active',
        )
        self.favorite = Favorite.objects.create(user=self.user, listing=self.listing)

    def test_remove_favorite_requires_post(self):
        self.client.login(username='favorite-user', password='FavoritePass123!')
        response = self.client.get(
            reverse('favorites:remove', kwargs={'favorite_id': self.favorite.id})
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Favorite.objects.filter(id=self.favorite.id).exists())

    def test_remove_favorite_post_deletes_own_favorite(self):
        self.client.login(username='favorite-user', password='FavoritePass123!')
        response = self.client.post(
            reverse('favorites:remove', kwargs={'favorite_id': self.favorite.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favorite.objects.filter(id=self.favorite.id).exists())


class SavedSearchAlertsTestCase(TestCase):
    """Tests for the saved-search alerts background job."""

    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        self.watcher = User.objects.create_user(
            username='ss-watcher', email='ss-watcher@example.com', password='WatchPass123!',
        )
        self.seller = User.objects.create_user(
            username='ss-seller', email='ss-seller@example.com', password='SellerPass123!',
        )
        self.category = Category.objects.create(name='SS Cat', slug='ss-cat', is_active=True)
        self.saved_search = SavedSearch.objects.create(
            user=self.watcher,
            name='Laptopuri ieftine',
            search_query='',
            category=self.category,
            max_price=1000,
            last_checked_at=timezone.now() - timedelta(hours=1),
        )

    def _create_listing(self, title, price, **kwargs):
        return Listing.objects.create(
            title=title,
            description='Test',
            price=price,
            owner=kwargs.pop('owner', self.seller),
            category=kwargs.pop('category', self.category),
            city='Cluj',
            status=kwargs.pop('status', 'active'),
            **kwargs,
        )

    def test_matching_listing_creates_notification(self):
        from notifications.models import Notification

        from .alerts import run_saved_search_alerts

        self._create_listing('Laptop bun', 800)
        result = run_saved_search_alerts()

        self.assertEqual(result['notified'], 1)
        notification = Notification.objects.get(recipient=self.watcher)
        self.assertEqual(notification.notification_type, 'new_listing_in_category')
        self.assertIn('Laptop bun', notification.message)
        self.assertIn('category=', notification.action_url)
        self.assertFalse(notification.is_emailed)

    def test_non_matching_and_own_listings_are_ignored(self):
        from notifications.models import Notification

        from .alerts import run_saved_search_alerts

        self._create_listing('Laptop scump', 5000)          # over max_price
        self._create_listing('Laptop propriu', 500, owner=self.watcher)  # own listing
        other_cat = Category.objects.create(name='SS Alt', slug='ss-alt', is_active=True)
        self._create_listing('Alt produs', 500, category=other_cat)      # other category

        result = run_saved_search_alerts()
        self.assertEqual(result['notified'], 0)
        self.assertFalse(Notification.objects.filter(recipient=self.watcher).exists())

    def test_watermark_prevents_duplicate_alerts(self):
        from notifications.models import Notification

        from .alerts import run_saved_search_alerts

        self._create_listing('Laptop bun', 800)
        run_saved_search_alerts()
        run_saved_search_alerts()

        self.assertEqual(Notification.objects.filter(recipient=self.watcher).count(), 1)

    def test_email_opt_out_suppresses_email_but_keeps_notification(self):
        from notifications.models import Notification

        from .alerts import run_saved_search_alerts

        self.saved_search.email_notifications = False
        self.saved_search.save(update_fields=['email_notifications'])
        self._create_listing('Laptop bun', 800)

        run_saved_search_alerts()
        notification = Notification.objects.get(recipient=self.watcher)
        self.assertTrue(notification.is_emailed)

    def test_periodic_command_queues_job_with_throttle(self):
        from io import StringIO

        from django.core.management import call_command

        from jobs.models import BackgroundJob

        call_command('enqueue_periodic_jobs', stdout=StringIO())
        self.assertEqual(
            BackgroundJob.objects.filter(name='favorites.saved_search_alerts').count(), 1,
        )

        # Second run: job already queued, so no duplicate.
        call_command('enqueue_periodic_jobs', stdout=StringIO())
        self.assertEqual(
            BackgroundJob.objects.filter(name='favorites.saved_search_alerts').count(), 1,
        )

    def test_job_handler_executes_via_registry(self):
        from jobs.models import BackgroundJob

        self._create_listing('Laptop bun', 800)
        job = BackgroundJob.enqueue('favorites.saved_search_alerts')
        claimed = BackgroundJob.claim_next()
        self.assertEqual(claimed.pk, job.pk)
        result = claimed.execute()
        self.assertEqual(result['notified'], 1)
        claimed.refresh_from_db()
        self.assertEqual(claimed.status, BackgroundJob.STATUS_SUCCEEDED)
