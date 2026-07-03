"""Versioned public API (/api/v1/) built with django-ninja.

Authentication for write endpoints: a personal API key sent as
``Authorization: Bearer mk_<prefix>_<secret>`` or an authenticated browser
session (used by the interactive docs at /api/v1/docs). API keys are managed
only through session-authenticated endpoints, so a leaked key cannot mint
new keys.
"""
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from ninja.security import HttpBearer, django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from categories.models import Category
from favorites.models import Favorite
from listings.forms import ListingForm
from listings.models import Listing
from listings.moderation import apply_listing_risk_review

from .filters import filter_listing_queryset
from .models import ApiKey
from .views import _listing_detail, _listing_summary

MAX_ACTIVE_KEYS_PER_USER = 5


class ApiKeyBearer(HttpBearer):
    def authenticate(self, request, token):
        user = ApiKey.authenticate_key(token)
        if user is None:
            return None
        request.user = user
        return user


api = NinjaAPI(
    title="Micu's Market API",
    version="1.0.0",
    description=(
        "Public API for the Micu's Market marketplace. Read endpoints are "
        "open; write endpoints need an API key (`Authorization: Bearer "
        "mk_...`) or a logged-in session. Manage keys under `/keys` while "
        "logged in on the site."
    ),
    urls_namespace="api_v1",
    throttle=[
        AnonRateThrottle(settings.API_READ_RATE),
        AuthRateThrottle("300/m"),
    ],
)

AUTH_ANY = [ApiKeyBearer(), django_auth]


# ---------- Schemas ----------

class CategoryRefOut(Schema):
    id: int | None = None
    name: str | None = None
    slug: str | None = None


class CategoryOut(Schema):
    id: int
    name: str
    slug: str
    icon: str = ""
    parent_id: int | None = None


class OwnerOut(Schema):
    username: str | None = None
    display_name: str | None = None


class ListingSummaryOut(Schema):
    id: int
    slug: str
    title: str
    price: str
    negotiable: bool
    condition: str
    city: str
    county: str
    category: CategoryRefOut
    owner: OwnerOut
    main_image: str | None = None
    views_count: int
    is_featured: bool
    is_promoted: bool
    created_at: str
    url: str


class ListingImageOut(Schema):
    id: int
    url: str | None = None
    alt_text: str
    order: int


class ListingDetailOut(ListingSummaryOut):
    description: str
    location: str | None = None
    images: list[ListingImageOut]
    is_favorited: bool
    updated_at: str


class ListingListOut(Schema):
    count: int
    page: int
    per_page: int
    num_pages: int
    has_next: bool
    has_previous: bool
    results: list[ListingSummaryOut]


class ListingCreateIn(Schema):
    title: str
    description: str
    price: str
    category_id: int | None = None
    city: str = "București"
    county: str = "București"
    location: str = ""
    contact_phone: str = ""
    condition: str = "good"
    negotiable: bool = True


class FavoriteToggleIn(Schema):
    listing_id: int


class FavoriteToggleOut(Schema):
    listing_id: int
    is_favorited: bool
    favorites_count: int


class MeOut(Schema):
    username: str
    email: str
    display_name: str
    is_verified: bool
    active_listings: int


class ApiKeyOut(Schema):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: str
    last_used_at: str | None = None


class ApiKeyCreateIn(Schema):
    name: str = ""


class ApiKeyCreatedOut(ApiKeyOut):
    key: str


class ErrorOut(Schema):
    detail: str


# ---------- Listings ----------

@api.get("/listings", response=ListingListOut, tags=["listings"])
def list_listings(
    request,
    q: str | None = None,
    category: str | None = None,
    city: str | None = None,
    seller: str | None = None,
    min_price: str | None = None,
    max_price: str | None = None,
    sort: str | None = None,
    page: int = 1,
    per_page: int = 20,
):
    """Search and filter active listings (paginated)."""
    params = {
        "q": q,
        "category": category,
        "city": city,
        "seller": seller,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
    }
    listings, _search_applied, _sort_by = filter_listing_queryset(params)

    per_page = min(max(per_page, 1), 50)
    paginator = Paginator(listings, per_page)
    page_obj = paginator.get_page(page)

    return {
        "count": paginator.count,
        "page": page_obj.number,
        "per_page": per_page,
        "num_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "results": [_listing_summary(request, listing) for listing in page_obj],
    }


@api.get("/listings/{slug}", response={200: ListingDetailOut, 404: ErrorOut}, tags=["listings"])
def get_listing(request, slug: str):
    """Retrieve one active listing by slug."""
    listing = get_object_or_404(
        Listing.objects.select_related("category", "owner").prefetch_related("images"),
        slug=slug,
        status="active",
    )
    return 200, _listing_detail(request, listing)


@api.post(
    "/listings",
    response={201: ListingDetailOut, 400: dict},
    auth=AUTH_ANY,
    throttle=[AuthRateThrottle(settings.API_WRITE_RATE)],
    tags=["listings"],
)
def create_listing(request, payload: ListingCreateIn):
    """Create a listing owned by the authenticated user."""
    data = payload.dict()
    data["category"] = data.pop("category_id")
    form = ListingForm(data)
    if not form.is_valid():
        return 400, {"errors": form.errors}

    listing = form.save(commit=False)
    listing.owner = request.auth
    listing.save()
    apply_listing_risk_review(listing, request.auth, request=request)
    return 201, _listing_detail(request, listing)


# ---------- Favorites ----------

@api.post(
    "/favorites/toggle",
    response={200: FavoriteToggleOut, 400: ErrorOut},
    auth=AUTH_ANY,
    throttle=[AuthRateThrottle(settings.API_WRITE_RATE)],
    tags=["favorites"],
)
def toggle_favorite(request, payload: FavoriteToggleIn):
    """Add or remove a listing from the authenticated user's favorites."""
    listing = get_object_or_404(Listing, id=payload.listing_id, status="active")
    if listing.owner == request.auth:
        return 400, {"detail": "Cannot favorite your own listing"}

    favorite, created = Favorite.objects.get_or_create(user=request.auth, listing=listing)
    if not created:
        favorite.delete()

    return 200, {
        "listing_id": listing.id,
        "is_favorited": created,
        "favorites_count": Favorite.objects.filter(user=request.auth).count(),
    }


# ---------- Categories ----------

@api.get("/categories", response=list[CategoryOut], tags=["categories"])
def list_categories(request):
    """All active categories (flat list; use parent_id to rebuild the tree)."""
    return list(
        Category.objects.filter(is_active=True)
        .order_by("parent_id", "order", "name")
        .values("id", "name", "slug", "icon", "parent_id")
    )


# ---------- Account ----------

@api.get("/me", response=MeOut, auth=AUTH_ANY, tags=["account"])
def me(request):
    """Details about the authenticated account."""
    user = request.auth
    profile = getattr(user, "profile", None)
    return {
        "username": user.username,
        "email": user.email,
        "display_name": user.get_full_name() or user.username,
        "is_verified": bool(profile and profile.is_verified),
        "active_listings": Listing.objects.filter(owner=user, status="active").count(),
    }


# ---------- API keys (session-only management) ----------

def _key_payload(key):
    return {
        "id": key.id,
        "name": key.name,
        "prefix": key.prefix,
        "is_active": key.is_active,
        "created_at": key.created_at.isoformat(),
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
    }


@api.get("/keys", response=list[ApiKeyOut], auth=django_auth, tags=["api-keys"])
def list_keys(request):
    """List your API keys (secrets are never shown again)."""
    return [_key_payload(key) for key in request.auth.api_keys.all()]


@api.post("/keys", response={201: ApiKeyCreatedOut}, auth=django_auth, tags=["api-keys"])
def create_key(request, payload: ApiKeyCreateIn):
    """Create an API key. The full secret is returned only once."""
    active_keys = request.auth.api_keys.filter(is_active=True).count()
    if active_keys >= MAX_ACTIVE_KEYS_PER_USER:
        raise HttpError(400, f"Maximum {MAX_ACTIVE_KEYS_PER_USER} active keys allowed.")

    key, raw_key = ApiKey.generate(request.auth, name=payload.name.strip()[:100])
    return 201, {**_key_payload(key), "key": raw_key}


@api.delete("/keys/{key_id}", response={204: None, 404: ErrorOut}, auth=django_auth, tags=["api-keys"])
def revoke_key(request, key_id: int):
    """Revoke one of your API keys."""
    key = get_object_or_404(ApiKey, id=key_id, user=request.auth)
    if key.is_active:
        key.revoke()
    return 204, None
