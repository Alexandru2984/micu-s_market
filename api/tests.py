import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
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

    def test_listing_list_ignores_invalid_price_filters(self):
        response = self.client.get(
            reverse('api:listing_list'),
            {'min_price': 'invalid', 'max_price': '-10'},
        )

        self.assertEqual(response.status_code, 200)
        slugs = [item['slug'] for item in response.json()['results']]
        self.assertIn(self.listing.slug, slugs)

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

    def test_listing_create_rejects_invalid_utf8_json(self):
        self.client.login(username='api-buyer', password='BuyerPass123!')
        response = self.client.post(
            reverse('api:listing_create'),
            data=b'\xff\xfe{',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid JSON')

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

    @override_settings(LISTING_RISK_REVIEW_THRESHOLD=70)
    def test_listing_create_api_applies_risk_review(self):
        self.client.login(username='api-buyer', password='BuyerPass123!')

        response = self.client.post(
            reverse('api:listing_create'),
            data=json.dumps(
                {
                    'title': 'Telefon whatsapp urgent',
                    'description': 'Plata in avans prin western union, discutam pe whatsapp.',
                    'category': self.category.id,
                    'price': '1.00',
                    'city': 'Iasi',
                    'county': 'Iasi',
                    'condition': 'good',
                    'negotiable': True,
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201, response.content)
        listing = Listing.objects.get(slug=response.json()['slug'])
        self.assertEqual(listing.status, 'inactive')
        self.assertTrue(listing.needs_moderation_review)
        self.assertGreaterEqual(listing.risk_score, 70)

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


class ApiV1Tests(TestCase):
    """Tests for the versioned django-ninja API under /api/v1/."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='v1-owner',
            email='v1-owner@example.com',
            password='OwnerPass123!',
        )
        self.buyer = User.objects.create_user(
            username='v1-buyer',
            email='v1-buyer@example.com',
            password='BuyerPass123!',
        )
        self.category = Category.objects.create(
            name='V1 Category',
            slug='v1-category',
            is_active=True,
        )
        self.listing = Listing.objects.create(
            title='Laptop V1',
            description='Laptop test v1',
            price=1500,
            owner=self.owner,
            category=self.category,
            city='Bucuresti',
            county='Bucuresti',
            status='active',
        )

    def _bearer(self, raw_key):
        return {'HTTP_AUTHORIZATION': f'Bearer {raw_key}'}

    def test_openapi_schema_is_served(self):
        response = self.client.get('/api/v1/openapi.json')
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema['info']['title'], "Micu's Market API")
        self.assertIn('/api/v1/listings', schema['paths'])

    def test_list_returns_only_active_listings(self):
        Listing.objects.create(
            title='Ascuns V1',
            description='inactiv',
            price=10,
            owner=self.owner,
            category=self.category,
            city='Cluj',
            status='inactive',
        )
        response = self.client.get('/api/v1/listings')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        slugs = [item['slug'] for item in payload['results']]
        self.assertIn(self.listing.slug, slugs)
        self.assertNotIn('ascuns-v1', slugs)

    def test_detail_404_for_inactive_listing(self):
        self.listing.status = 'inactive'
        self.listing.save(update_fields=['status'])
        response = self.client.get(f'/api/v1/listings/{self.listing.slug}')
        self.assertEqual(response.status_code, 404)

    def test_create_listing_requires_auth(self):
        response = self.client.post(
            '/api/v1/listings',
            data=json.dumps({'title': 'X', 'description': 'Y', 'price': '10'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_create_listing_with_api_key(self):
        from api.models import ApiKey

        _key, raw_key = ApiKey.generate(self.buyer, name='test')
        response = self.client.post(
            '/api/v1/listings',
            data=json.dumps({
                'title': 'Bicicleta V1',
                'description': 'Aproape noua',
                'price': '350.00',
                'category_id': self.category.id,
                'city': 'Brasov',
                'county': 'Brasov',
            }),
            content_type='application/json',
            **self._bearer(raw_key),
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['owner']['username'], 'v1-buyer')
        self.assertTrue(Listing.objects.filter(slug=payload['slug'], owner=self.buyer).exists())

    def test_invalid_and_revoked_keys_are_rejected(self):
        from api.models import ApiKey

        response = self.client.get('/api/v1/me', **self._bearer('mk_bad_key'))
        self.assertEqual(response.status_code, 401)

        key, raw_key = ApiKey.generate(self.buyer)
        key.revoke()
        response = self.client.get('/api/v1/me', **self._bearer(raw_key))
        self.assertEqual(response.status_code, 401)

    def test_favorite_toggle_with_api_key(self):
        from api.models import ApiKey

        _key, raw_key = ApiKey.generate(self.buyer)
        response = self.client.post(
            '/api/v1/favorites/toggle',
            data=json.dumps({'listing_id': self.listing.id}),
            content_type='application/json',
            **self._bearer(raw_key),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_favorited'])
        self.assertTrue(Favorite.objects.filter(user=self.buyer, listing=self.listing).exists())

    def test_me_with_session(self):
        self.client.login(username='v1-buyer', password='BuyerPass123!')
        response = self.client.get('/api/v1/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'v1-buyer')

    def test_key_management_requires_session_not_api_key(self):
        from api.models import ApiKey

        _key, raw_key = ApiKey.generate(self.buyer)
        response = self.client.post(
            '/api/v1/keys',
            data=json.dumps({'name': 'nope'}),
            content_type='application/json',
            **self._bearer(raw_key),
        )
        self.assertEqual(response.status_code, 401)

    def test_key_lifecycle_create_list_revoke(self):
        from api.models import ApiKey

        self.client.login(username='v1-buyer', password='BuyerPass123!')

        response = self.client.post(
            '/api/v1/keys',
            data=json.dumps({'name': 'cli'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload['key'].startswith('mk_'))
        key_id = payload['id']

        response = self.client.get('/api/v1/keys')
        self.assertEqual(response.status_code, 200)
        listed = response.json()
        self.assertEqual(len(listed), 1)
        self.assertNotIn('key', listed[0])

        response = self.client.delete(f'/api/v1/keys/{key_id}')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ApiKey.objects.get(pk=key_id).is_active)

    def test_active_key_limit_enforced(self):
        from api.models import ApiKey

        for _ in range(5):
            ApiKey.generate(self.buyer)
        self.client.login(username='v1-buyer', password='BuyerPass123!')
        response = self.client.post(
            '/api/v1/keys',
            data=json.dumps({'name': 'peste-limita'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
