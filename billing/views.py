from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from listings.models import Listing

from .models import PromotionOrder, PromotionPlan


@login_required
@require_http_methods(["GET", "POST"])
def promote_listing_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    plans = PromotionPlan.objects.filter(is_active=True)

    if request.method == "POST":
        plan = get_object_or_404(plans, pk=request.POST.get("plan"))
        order = PromotionOrder.objects.create(
            listing=listing,
            user=request.user,
            plan=plan,
            amount=plan.price,
            currency=plan.currency,
        )
        messages.success(request, "Comanda de promovare a fost creată. Marcheaz-o ca plătită din admin sau conectează un gateway.")
        return redirect("billing:promotion_order", pk=order.pk)

    return render(request, "billing/promote_listing.html", {"listing": listing, "plans": plans})


@login_required
def promotion_order_view(request, pk):
    order = get_object_or_404(
        PromotionOrder.objects.select_related("listing", "plan"),
        pk=pk,
        user=request.user,
    )
    return render(request, "billing/promotion_order.html", {"order": order})
