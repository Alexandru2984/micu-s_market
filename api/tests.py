import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from categories.models import Category
from favorites.models import Favorite
from listings.models import Listing

User = get_user_model()


class ListingApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='api-owner',
            email='owner@example.com',
            password='OwnerPass123!',
        )
        self.buyer = User.objects.create_user(
            username='api-buyer',
            email='buyer@example.com',
            password='BuyerPass123!',
        )
        self.category = Category.objects.create(
            name='API Category',
            slug='api-category',
            is_active=True,
        )
        self.child_category = Category.objects.create(
            name='API Child Category',
            slug='api-child-category',
            parent=self.category,
            is_active=True,
        )
        self.listing = Listing.objects.create(
            title='Telefon API',
            description='Telefon test API',
            price=500,
            owner=self.owner,
            category=self.category,
            city='Bucuresti',
            county='Bucuresti',
            status='active',
        )
        self.inactive_listing = Listing.objects.create(
            title='Ascuns API',
            description='Nu trebuie expus',
            price=100,
            owner=self.owner,
            category=self.category,
            city='Cluj',
            status='inactive',
        )
        self.child_listing = Listing.objects.create(
            title='Subcategorie API',
            description='Apare la filtrarea categoriei parinte',
            price=250,
            owner=self.owner,
            category=self.child_category,
            city='Brasov',
            status='active',
        )

    def test_listing_list_returns_only_active_listings(self):
        response = self.client.get(reverse('api:listing_list'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        slugs = [item['slug'] for item in payload['results']]
        self.assertIn(self.listing.slug, slugs)
        self.assertNotIn(self.inactive_listing.slug, slugs)

    def test_listing_detail_returns_public_listing_data(self):
        response = self.client.get(
            reverse('api:listing_detail', kwargs={'slug': self.listing.slug})
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['slug'], self.listing.slug)
        self.assertEqual(payload['category']['slug'], self.category.slug)
        self.assertFalse(payload['is_favorited'])

    def test_parent_category_filter_includes_child_categories(self):
        response = self.client.get(
            reverse('api:listing_list'),
            {'category': self.category.slug},
        )
        self.assertEqual(response.status_code, 200)
        slugs = [item['slug'] for item in response.json()['results']]
        self.assertIn(self.listing.slug, slugs)
        self.assertIn(self.child_listing.slug, slugs)

    def test_search_orders_results_by_relevance(self):
        relevant = Listing.objects.create(
            title='Laptop gaming Asus ROG',
            description='Placă video dedicată și ecran rapid',
            price=3500,
            owner=self.owner,
            category=self.category,
            city='Iasi',
            status='active',
        )
        Listing.objects.create(
            title='Husă laptop',
            description='Accesoriu simplu pentru transport, fără gaming',
            price=80,
            owner=self.owner,
            category=self.category,
            city='Iasi',
            status='active',
        )

        response = self.client.get(reverse('api:listing_list'), {'q': 'laptop gaming'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['slug'], relevant.slug)

    def test_search_tolerates_small_typos(self):
        Listing.objects.create(
            title='Bicicletă electrică pliabilă',
            description='Autonomie bună pentru oraș',
            price=2200,
            owner=self.owner,
            category=self.category,
            city='Timisoara',
            status='active',
        )

        response = self.client.get(reverse('api:listing_list'), {'q': 'bicicleta electrica'})

        self.assertEqual(response.status_code, 200)
        slugs = [item['slug'] for item in response.json()['results']]
        self.assertIn('bicicleta-electrica-pliabila', slugs)

    def test_listing_create_requires_authentication(self):
        response = self.client.post(
            reverse('api:listing_create'),
            data=json.dumps({'title': 'Nou'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_listing(self):
        self.client.login(username='api-buyer', password='BuyerPass123!')
        response = self.client.post(
            reverse('api:listing_create'),
            data=json.dumps(
                {
                    'title': 'Laptop API',
                    'description': 'Laptop creat prin API',
                    'category': self.category.id,
                    'price': '1200.00',
                    'city': 'Iasi',
                    'county': 'Iasi',
                    'condition': 'good',
                    'negotiable': True,
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        listing = Listing.objects.get(slug=payload['slug'])
        self.assertEqual(listing.owner, self.buyer)
        self.assertEqual(payload['title'], 'Laptop API')

    def test_favorite_toggle_requires_authentication(self):
        response = self.client.post(
            reverse('api:favorite_toggle'),
            data=json.dumps({'listing_id': self.listing.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_favorite_toggle_adds_and_removes_favorite(self):
        self.client.login(username='api-buyer', password='BuyerPass123!')
        url = reverse('api:favorite_toggle')

        response = self.client.post(
            url,
            data=json.dumps({'listing_id': self.listing.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_favorited'])
        self.assertTrue(Favorite.objects.filter(user=self.buyer, listing=self.listing).exists())

        response = self.client.post(
            url,
            data=json.dumps({'listing_id': self.listing.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_favorited'])
        self.assertFalse(Favorite.objects.filter(user=self.buyer, listing=self.listing).exists())

    def test_user_cannot_favorite_own_listing(self):
        self.client.login(username='api-owner', password='OwnerPass123!')
        response = self.client.post(
            reverse('api:favorite_toggle'),
            data=json.dumps({'listing_id': self.listing.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
