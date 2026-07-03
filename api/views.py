import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit

from favorites.models import Favorite
from listings.forms import ListingForm
from listings.models import Listing
from listings.moderation import apply_listing_risk_review

from .filters import filter_listing_queryset


def _json_body(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    return request.POST


def _auth_required(request):
    if request.user.is_authenticated:
        return None
    return JsonResponse({'error': 'Authentication required'}, status=401)


def _absolute_url(request, path):
    return request.build_absolute_uri(path)


def _image_url(request, image):
    if not image:
        return None
    return _absolute_url(request, image.url)


def _listing_summary(request, listing):
    main_image = listing.main_image
    return {
        'id': listing.id,
        'slug': listing.slug,
        'title': listing.title,
        'price': str(listing.price),
        'negotiable': listing.negotiable,
        'condition': listing.condition,
        'city': listing.city,
        'county': listing.county,
        'category': {
            'id': listing.category_id,
            'name': listing.category.name if listing.category else None,
            'slug': listing.category.slug if listing.category else None,
        },
        'owner': {
            'username': listing.owner.username if listing.owner else None,
            'display_name': listing.owner.get_full_name() if listing.owner else None,
        },
        'main_image': _image_url(request, main_image),
        'views_count': listing.views_count,
        'is_featured': listing.is_featured,
        'is_promoted': listing.is_promoted,
        'created_at': listing.created_at.isoformat(),
        'url': _absolute_url(request, reverse('listings:detail', kwargs={'slug': listing.slug})),
    }


def _listing_detail(request, listing):
    data = _listing_summary(request, listing)
    data.update(
        {
            'description': listing.description,
            'location': listing.location,
            'images': [
                {
                    'id': image.id,
                    'url': _image_url(request, image.image),
                    'alt_text': image.alt_text,
                    'order': image.order,
                }
                for image in listing.images.all()
            ],
            'is_favorited': (
                request.user.is_authenticated
                and Favorite.objects.filter(user=request.user, listing=listing).exists()
            ),
            'updated_at': listing.updated_at.isoformat(),
        }
    )
    return data


@require_GET
@ratelimit(key='ip', rate=settings.API_READ_RATE, method='GET', block=True)
def listing_list_api(request):
    listings, _search_applied, _sort_by = filter_listing_queryset(request.GET)

    page_number = request.GET.get('page', 1)
    try:
        per_page = min(max(int(request.GET.get('per_page', 20)), 1), 50)
    except ValueError:
        per_page = 20

    paginator = Paginator(listings, per_page)
    page_obj = paginator.get_page(page_number)

    return JsonResponse(
        {
            'count': paginator.count,
            'page': page_obj.number,
            'per_page': per_page,
            'num_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': [_listing_summary(request, listing) for listing in page_obj],
        }
    )


@require_GET
@ratelimit(key='ip', rate=settings.API_READ_RATE, method='GET', block=True)
def listing_detail_api(request, slug):
    listing = get_object_or_404(
        Listing.objects.select_related('category', 'owner').prefetch_related('images'),
        slug=slug,
        status='active',
    )
    return JsonResponse(_listing_detail(request, listing))


@require_POST
@ratelimit(key='ip', rate=settings.API_WRITE_RATE, method='POST', block=True)
def listing_create_api(request):
    auth_response = _auth_required(request)
    if auth_response:
        return auth_response

    payload = _json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    form = ListingForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    listing = form.save(commit=False)
    listing.owner = request.user
    listing.save()
    apply_listing_risk_review(listing, request.user, request=request)
    return JsonResponse(_listing_detail(request, listing), status=201)


@require_POST
@ratelimit(key='ip', rate=settings.API_WRITE_RATE, method='POST', block=True)
def favorite_toggle_api(request):
    auth_response = _auth_required(request)
    if auth_response:
        return auth_response

    payload = _json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    listing_id = payload.get('listing_id')
    if not listing_id:
        return JsonResponse({'error': 'listing_id is required'}, status=400)

    listing = get_object_or_404(Listing, id=listing_id, status='active')
    if listing.owner == request.user:
        return JsonResponse({'error': 'Cannot favorite your own listing'}, status=400)

    favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if created:
        is_favorited = True
    else:
        favorite.delete()
        is_favorited = False

    return JsonResponse(
        {
            'listing_id': listing.id,
            'is_favorited': is_favorited,
            'favorites_count': Favorite.objects.filter(user=request.user).count(),
        }
    )
