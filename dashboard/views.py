from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.utils import timezone

from listings.models import Listing, ListingReport

# Create your views here.

@login_required
@staff_member_required
def dashboard_home_view(request):
	context = {}
	return render(request, 'dashboard/home.html', context)

@login_required
@staff_member_required
def reports_list_view(request):
	context = {}
	return render(request, 'dashboard/reports.html', context)

@login_required
@staff_member_required
def verify_listings_view(request):
	context = {}
	return render(request, 'dashboard/verify_listings.html', context)


@login_required
def seller_insights_view(request):
    now = timezone.now()
    base_listings = Listing.objects.filter(owner=request.user)
    top_listings = (
        base_listings
        .annotate(
            favorite_count=Count("favorited_by", distinct=True),
            report_count=Count("reports", distinct=True),
        )
        .order_by("-views_count", "-favorite_count", "-created_at")
    )

    stats = base_listings.aggregate(
        total_listings=Count("id"),
        active_listings=Count("id", filter=Q(status="active")),
        sold_listings=Count("id", filter=Q(status="sold")),
        total_views=Sum("views_count"),
        total_favorites=Count("favorited_by", distinct=True),
        active_promotions=Count(
            "id",
            filter=Q(is_featured=True) & (Q(featured_until__isnull=True) | Q(featured_until__gt=now)),
        ),
    )

    open_reports = (
        ListingReport.objects.filter(
            listing__owner=request.user,
            status__in=["pending", "reviewed"],
        )
        .select_related("listing", "reporter")
        .order_by("-created_at")[:5]
    )

    context = {
        "stats": {
            "total_listings": stats["total_listings"] or 0,
            "active_listings": stats["active_listings"] or 0,
            "sold_listings": stats["sold_listings"] or 0,
            "total_views": stats["total_views"] or 0,
            "total_favorites": stats["total_favorites"] or 0,
            "active_promotions": stats["active_promotions"] or 0,
        },
        "top_listings": top_listings[:8],
        "open_reports": open_reports,
    }
    return render(request, "dashboard/seller_insights.html", context)
