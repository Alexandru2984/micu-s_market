"""
Teste pentru sistemul de recenzii — prevenire self-review, duplicate, access control
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Review
from listings.models import Listing
from categories.models import Category

User = get_user_model()


class ReviewSecurityTestCase(TestCase):
    """Teste de securitate pentru review-uri"""

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

    def test_cannot_review_yourself(self):
        """Utilizatorul nu poate lăsa o recenzie pentru sine însuși"""
        self.client.login(username='reviewer', password='ReviewPass123!')
        response = self.client.post(
            reverse('reviews:create_review', kwargs={'username': self.reviewer.username}),
            {
                'title': 'Self review',
                'content': 'Test',
                'rating': 5
            }
        )
        # Trebuie redirecționat cu eroare, NU creat review
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(reviewer=self.reviewer, reviewed_user=self.reviewer).exists())

    def test_duplicate_review_prevented(self):
        """Nu se pot lăsa două review-uri pentru același utilizator/anunț"""
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
        # Trebuie redirecționat cu warning
        self.assertEqual(response.status_code, 302)
        # Trebuie să existe un singur review
        self.assertEqual(
            Review.objects.filter(reviewer=self.reviewer, reviewed_user=self.reviewed).count(),
            1
        )

    def test_create_review_requires_login(self):
        """Crearea de review-uri necesită autentificare"""
        response = self.client.get(
            reverse('reviews:create_review', kwargs={'username': self.reviewed.username})
        )
        self.assertEqual(response.status_code, 302)

    def test_my_reviews_requires_login(self):
        """Pagina 'review-urile mele' necesită autentificare"""
        response = self.client.get(reverse('reviews:my_reviews'))
        self.assertEqual(response.status_code, 302)

    def test_delete_review_only_by_author(self):
        """Doar autorul poate șterge propriul review"""
        review = Review.objects.create(
            reviewer=self.reviewer,
            reviewed_user=self.reviewed,
            listing=self.listing,
            title='Test review',
            comment='Test',
            transaction_type='purchase',
            rating=3
        )
        # Alt user încearcă să șteargă
        self.client.login(username='reviewed', password='ReviewedPass123!')
        response = self.client.post(
            reverse('reviews:delete_review', kwargs={'review_id': review.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
