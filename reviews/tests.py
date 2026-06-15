"""
Tests for the reviews system — preventing self-review, duplicates, access control
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Review
from listings.models import Listing
from categories.models import Category

User = get_user_model()


class ReviewSecurityTestCase(TestCase):
    """Security tests for reviews"""

    def setUp(self):
        self.client = Client()
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='ReviewPass123!'
        )
        self.reviewed = User.objects.create_user(
            username='reviewed',
            email='reviewed@example.com',
            password='ReviewedPass123!'
        )
        self.category = Category.objects.create(
            name='Review Test Cat',
            slug='review-test-cat',
            is_active=True
        )
        self.listing = Listing.objects.create(
            title='Produs recenzie',
            description='Test',
            price=50.00,
            owner=self.reviewed,
            category=self.category,
            city='Iași',
            status='active'
        )
        self.other_listing_owner = User.objects.create_user(
            username='other-owner',
            email='other-owner@example.com',
            password='OtherPass123!'
        )
        self.other_listing = Listing.objects.create(
            title='Alt produs',
            description='Test',
            price=75.00,
            owner=self.other_listing_owner,
            category=self.category,
            city='Cluj',
            status='active',
        )

    def test_cannot_review_yourself(self):
        """A user cannot leave a review for themselves"""
        self.client.login(username='reviewer', password='ReviewPass123!')
        response = self.client.post(
            reverse('reviews:create_review', kwargs={'username': self.reviewer.username}),
            {
                'title': 'Self review',
                'content': 'Test',
                'rating': 5
            }
        )
        # Must redirect with an error, NOT create a review
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(reviewer=self.reviewer, reviewed_user=self.reviewer).exists())

    def test_duplicate_review_prevented(self):
        """Two reviews cannot be left for the same user/listing"""
        Review.objects.create(
            reviewer=self.reviewer,
            reviewed_user=self.reviewed,
            listing=self.listing,
            title='Primul review',
            comment='Bun',
            transaction_type='purchase',
            rating=4
        )
        self.client.login(username='reviewer', password='ReviewPass123!')
        response = self.client.post(
            reverse('reviews:create_review', kwargs={'username': self.reviewed.username}) +
            f'?listing={self.listing.slug}',
            {
                'title': 'Al doilea review',
                'content': 'Test duplicat',
                'rating': 1
            }
        )
        # Must redirect with a warning
        self.assertEqual(response.status_code, 302)
        # Only a single review must exist
        self.assertEqual(
            Review.objects.filter(reviewer=self.reviewer, reviewed_user=self.reviewed).count(),
            1
        )

    def test_review_listing_must_belong_to_reviewed_user(self):
        """A review cannot be attached to another user's listing."""
        self.client.login(username='reviewer', password='ReviewPass123!')
        response = self.client.post(
            reverse('reviews:create_review', kwargs={'username': self.reviewed.username}) +
            f'?listing={self.other_listing.slug}',
            {
                'title': 'Review greșit',
                'comment': 'Atașare invalidă',
                'transaction_type': 'purchase',
                'rating': 5,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Review.objects.filter(
                reviewer=self.reviewer,
                reviewed_user=self.reviewed,
                listing=self.other_listing,
            ).exists()
        )

    def test_create_review_requires_login(self):
        """Creating reviews requires authentication"""
        response = self.client.get(
            reverse('reviews:create_review', kwargs={'username': self.reviewed.username})
        )
        self.assertEqual(response.status_code, 302)

    def test_my_reviews_requires_login(self):
        """The 'my reviews' page requires authentication"""
        response = self.client.get(reverse('reviews:my_reviews'))
        self.assertEqual(response.status_code, 302)

    def test_review_stats_api_requires_get(self):
        response = self.client.post(
            reverse('reviews:stats_api', kwargs={'username': self.reviewed.username})
        )

        self.assertEqual(response.status_code, 405)

    def test_delete_review_only_by_author(self):
        """Only the author can delete their own review"""
        review = Review.objects.create(
            reviewer=self.reviewer,
            reviewed_user=self.reviewed,
            listing=self.listing,
            title='Test review',
            comment='Test',
            transaction_type='purchase',
            rating=3
        )
        # A different user tries to delete it
        self.client.login(username='reviewed', password='ReviewedPass123!')
        response = self.client.post(
            reverse('reviews:delete_review', kwargs={'review_id': review.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

    def test_delete_review_recalculates_profile_rating(self):
        """Deleting a review updates the profile's public rating."""
        review = Review.objects.create(
            reviewer=self.reviewer,
            reviewed_user=self.reviewed,
            listing=self.listing,
            title='Test review',
            comment='Test',
            transaction_type='purchase',
            rating=5,
        )
        self.reviewed.profile.refresh_from_db()
        self.assertEqual(self.reviewed.profile.average_rating, 5)

        review.delete()

        self.reviewed.profile.refresh_from_db()
        self.assertEqual(self.reviewed.profile.average_rating, 0)

    def test_bulk_delete_review_recalculates_profile_rating(self):
        """Bulk deletes from admin/queryset update the profile rating."""
        Review.objects.create(
            reviewer=self.reviewer,
            reviewed_user=self.reviewed,
            listing=self.listing,
            title='Test review',
            comment='Test',
            transaction_type='purchase',
            rating=5,
        )
        self.reviewed.profile.refresh_from_db()
        self.assertEqual(self.reviewed.profile.average_rating, 5)

        Review.objects.filter(reviewed_user=self.reviewed).delete()

        self.reviewed.profile.refresh_from_db()
        self.assertEqual(self.reviewed.profile.average_rating, 0)
