import re

from django.conf import settings
from django.utils import timezone

from audit.utils import audit_log
from notifications.models import Notification


PHONE_RE = re.compile(r"(?<!\d)(?:\+?4?0|0)?(?:\s|-|\.)?\d(?:\s|-|\.?\d){7,}(?!\d)")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


def evaluate_listing_risk(listing, user):
    text = " ".join(
        str(value or "")
        for value in (listing.title, listing.description, listing.city, listing.county, listing.location)
    ).lower()
    reasons = []
    score = 0

    matched_terms = [term for term in settings.LISTING_RISK_TERMS if term and term.lower() in text]
    if matched_terms:
        score += min(len(matched_terms) * 35, 70)
        reasons.append(f"Termeni sensibili: {', '.join(sorted(set(matched_terms)))}")

    if PHONE_RE.search(listing.description or "") and not listing.contact_phone:
        score += 20
        reasons.append("Număr de telefon în descriere fără câmp contact dedicat")

    if URL_RE.search(listing.description or ""):
        score += 20
        reasons.append("Link extern în descriere")

    profile = getattr(user, "profile", None)
    if profile and not profile.is_verified:
        score += 10
        reasons.append("Vânzător neverificat")

    if user.date_joined and user.date_joined > timezone.now() - timezone.timedelta(days=1):
        score += 15
        reasons.append("Cont creat recent")

    if listing.price and listing.price <= 1:
        score += 20
        reasons.append("Preț neobișnuit de mic")

    return min(score, 100), reasons


def apply_listing_risk_review(listing, user, request=None):
    score, reasons = evaluate_listing_risk(listing, user)
    threshold = settings.LISTING_RISK_REVIEW_THRESHOLD
    needs_review = score >= threshold
    note = "\n".join(reasons)

    update_fields = ["risk_score", "needs_moderation_review", "moderation_note", "updated_at"]
    listing.risk_score = score
    listing.needs_moderation_review = needs_review
    listing.moderation_note = note

    if needs_review and listing.status == "active":
        listing.status = "inactive"
        update_fields.append("status")

    listing.save(update_fields=update_fields)

    if needs_review:
        audit_log("listing.risk_review_required", request=request, obj=listing, metadata={"score": score, "reasons": reasons})
        Notification.objects.get_or_create(
            recipient=listing.owner,
            notification_type="listing_rejected",
            related_object_type="Listing",
            related_object_id=listing.pk,
            defaults={
                "title": "Anunț trimis la moderare",
                "message": "Anunțul tău a fost ascuns temporar pentru verificări de siguranță.",
                "action_url": listing.get_absolute_url(),
            },
        )

    return score, reasons
