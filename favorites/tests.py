from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from categories.models import Category
from listings.models import Listing
from .models import Favorite

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
