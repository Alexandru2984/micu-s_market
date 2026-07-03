"""Shared listing filtering for the legacy JSON views and the v1 API."""
from decimal import Decimal, InvalidOperation

from categories.models import Category
from listings.models import Listing
from listings.search import apply_listing_search, order_search_results

VALID_SORTS = {"relevance", "-created_at", "created_at", "price", "-price", "title", "-title"}


def _apply_decimal_filter(queryset, field_name, raw_value, lookup):
    if raw_value in (None, ""):
        return queryset
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        return queryset
    if value < 0:
        return queryset
    return queryset.filter(**{f"{field_name}__{lookup}": value})


def _resolve_category(raw_value):
    if not raw_value:
        return None
    try:
        return Category.objects.get(slug=raw_value, is_active=True)
    except Category.DoesNotExist:
        pass
    if str(raw_value).isdigit():
        try:
            return Category.objects.get(id=int(raw_value), is_active=True)
        except Category.DoesNotExist:
            pass
    return None


def filter_listing_queryset(params):
    """Filter and sort active listings from a dict-like of query params.

    Returns ``(queryset, search_applied, sort_by)``.
    """
    listings = (
        Listing.objects.filter(status="active")
        .select_related("category", "owner")
        .prefetch_related("images")
    )

    seller = params.get("seller")
    if seller:
        listings = listings.filter(owner__username=seller)

    category = _resolve_category(params.get("category"))
    if category:
        category_ids = [category.id] + [child.id for child in category.get_all_children]
        listings = listings.filter(category_id__in=category_ids)

    city = params.get("city")
    if city:
        listings = listings.filter(city__icontains=city)

    query = params.get("q") or params.get("search")
    listings, search_applied = apply_listing_search(listings, query)

    listings = _apply_decimal_filter(listings, "price", params.get("min_price"), "gte")
    listings = _apply_decimal_filter(listings, "price", params.get("max_price"), "lte")

    sort_by = params.get("sort") or ("relevance" if search_applied else "-created_at")
    if sort_by not in VALID_SORTS:
        sort_by = "-created_at"
    listings = order_search_results(listings, sort_by, search_applied)
    if sort_by != "relevance":
        listings = listings.order_by(sort_by)

    return listings, search_applied, sort_by
