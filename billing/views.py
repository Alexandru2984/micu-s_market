import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from audit.utils import audit_log
from listings.models import Listing

from .models import PaymentWebhookEvent, PromotionOrder, PromotionPlan


@login_required
@require_http_methods(["GET", "POST"])
@ratelimit(key="user", rate=settings.BILLING_ORDER_RATE, method="POST", block=True)
def promote_listing_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, owner=request.user, status="active")
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


@csrf_exempt
@require_POST
def promotion_webhook_view(request):
    """Signed payment webhook for promotion orders.

    Expected JSON fields: event_id, order_id, status. The signature is
    HMAC-SHA256 over "<timestamp>.<raw_body>" using BILLING_WEBHOOK_SECRET.
    """
    if not settings.BILLING_WEBHOOK_SECRET:
        return JsonResponse({"error": "webhook_not_configured"}, status=503)

    if not _valid_webhook_signature(request):
        return JsonResponse({"error": "invalid_signature"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)

    event_id = str(payload.get("event_id", "")).strip()
    order_id = payload.get("order_id")
    payment_status = str(payload.get("status", "")).strip().lower()
    provider = str(payload.get("provider") or "generic").strip()[:50] or "generic"
    external_reference = str(payload.get("external_reference", "")).strip()

    if not event_id or not order_id or payment_status not in {"paid", "cancelled"}:
        return JsonResponse({"error": "invalid_payload"}, status=400)

    with transaction.atomic():
        event, created = PaymentWebhookEvent.objects.get_or_create(
            provider=provider,
            event_id=event_id,
            defaults={"payload": payload},
        )
        if not created:
            return JsonResponse({"ok": True, "duplicate": True, "event_id": event.event_id})

        order = get_object_or_404(PromotionOrder.objects.select_for_update(), pk=order_id)
        event.order = order

        if external_reference and not order.external_reference:
            order.external_reference = external_reference
            order.save(update_fields=["external_reference"])

        applied = False
        if payment_status == "paid":
            order.mark_paid()
            applied = order.apply_promotion()
            event.status = "processed"
            audit_log("billing.webhook_paid", request=request, obj=order, metadata={"event_id": event_id})
        elif payment_status == "cancelled":
            if order.status == "pending":
                order.status = "cancelled"
                order.save(update_fields=["status"])
            event.status = "processed"
            audit_log("billing.webhook_cancelled", request=request, obj=order, metadata={"event_id": event_id})

        event.processed_at = timezone.now()
        event.save(update_fields=["order", "status", "processed_at"])

    return JsonResponse({"ok": True, "event_id": event_id, "order_id": order.pk, "applied": applied})


def _valid_webhook_signature(request):
    timestamp = request.headers.get("X-Micu-Timestamp", "")
    signature = request.headers.get("X-Micu-Signature", "")
    if signature.startswith("sha256="):
        signature = signature.removeprefix("sha256=")

    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    tolerance = settings.BILLING_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS
    if abs(time.time() - timestamp_int) > tolerance:
        return False

    signed_payload = timestamp.encode("utf-8") + b"." + request.body
    expected = hmac.new(
        settings.BILLING_WEBHOOK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
