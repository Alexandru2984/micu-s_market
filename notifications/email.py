import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


EMAIL_TYPE_PREFERENCES = {
    "new_message": "email_new_messages",
    "new_review": "email_new_reviews",
    "listing_sold": "email_listing_updates",
    "listing_expired": "email_listing_updates",
    "listing_approved": "email_listing_updates",
    "listing_rejected": "email_listing_updates",
    "price_alert": "email_price_alerts",
    "account_verification": "email_listing_updates",
    "system": "email_listing_updates",
}


def should_email(notification):
    preference_name = EMAIL_TYPE_PREFERENCES.get(notification.notification_type)
    if not preference_name:
        return False
    preferences = getattr(notification.recipient, "notification_preferences", None)
    return bool(preferences and getattr(preferences, preference_name, False))


def send_notification_email(notification):
    if notification.is_emailed or not notification.recipient.email or not should_email(notification):
        return False

    context = {"notification": notification, "site_name": "Micu's Market"}
    subject = f"[Micu's Market] {notification.title}"
    text_body = render_to_string("notifications/email/notification.txt", context)
    html_body = render_to_string("notifications/email/notification.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notification.recipient.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send()

    notification.is_emailed = True
    notification.save(update_fields=["is_emailed"])
    logger.info("notification_email_sent", extra={"notification_id": notification.pk})
    return True


def send_pending_notification_emails(limit=100):
    from notifications.models import Notification

    notifications = (
        Notification.objects.filter(is_emailed=False)
        .select_related("recipient", "recipient__notification_preferences")
        .order_by("created_at")[:limit]
    )

    sent = 0
    for notification in notifications:
        if send_notification_email(notification):
            sent += 1
    return sent
