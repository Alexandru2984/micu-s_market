"""Saved-search alerts: notify users when new listings match their searches."""
import logging
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone

from api.filters import filter_listing_queryset
from notifications.models import Notification

from .models import SavedSearch

logger = logging.getLogger(__name__)

MAX_TITLES_IN_MESSAGE = 3


def _results_url(saved_search):
    params = saved_search.get_search_params()
    query = {}
    if params.get("q"):
        query["search"] = params["q"]
    if params.get("category"):
        query["category"] = params["category"]
    for key in ("min_price", "max_price", "city"):
        if params.get(key):
            query[key] = params[key]
    url = reverse("listings:list")
    return f"{url}?{urlencode(query)}" if query else url


def _new_matches(saved_search, since):
    listings, _search_applied, _sort_by = filter_listing_queryset(saved_search.get_search_params())
    listings = listings.filter(
        created_at__gt=since,
        needs_moderation_review=False,
    ).exclude(owner=saved_search.user)
    if saved_search.county:
        listings = listings.filter(county__icontains=saved_search.county)
    return listings.order_by("-created_at")


def run_saved_search_alerts(limit_per_search=20):
    """Check every active saved search for new listings and notify the owner.

    Returns a summary dict for the background-job result payload.
    """
    run_started = timezone.now()
    checked = 0
    notified = 0

    saved_searches = SavedSearch.objects.filter(is_active=True).select_related("user", "category")
    for saved_search in saved_searches:
        matches = list(_new_matches(saved_search, saved_search.last_checked_at)[:limit_per_search])
        checked += 1

        if matches:
            titles = ", ".join(f'"{listing.title}"' for listing in matches[:MAX_TITLES_IN_MESSAGE])
            extra = len(matches) - MAX_TITLES_IN_MESSAGE
            if extra > 0:
                titles += f" și încă {extra}"
            Notification.objects.create(
                recipient=saved_search.user,
                notification_type="new_listing_in_category",
                title=f"Anunțuri noi pentru „{saved_search.name}”",
                message=f"Au apărut anunțuri noi care se potrivesc căutării tale: {titles}.",
                related_object_type="SavedSearch",
                related_object_id=saved_search.pk,
                action_url=_results_url(saved_search),
                # Respect the per-search email opt-out while keeping the
                # in-app notification: already-emailed items are skipped
                # by the email dispatcher.
                is_emailed=not saved_search.email_notifications,
            )
            notified += 1
            logger.info(
                "saved_search_alert",
                extra={"saved_search_id": saved_search.pk, "matches": len(matches)},
            )

        SavedSearch.objects.filter(pk=saved_search.pk).update(last_checked_at=run_started)

    return {"checked": checked, "notified": notified}
