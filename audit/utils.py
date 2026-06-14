import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import AuditEvent

logger = logging.getLogger("audit")
User = get_user_model()


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for and getattr(settings, "TRUSTED_PROXY_CHAIN_CONFIGURED", False):
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR")


def audit_log(event_type, request=None, actor=None, obj=None, metadata=None):
    if request is not None and actor is None and getattr(request, "user", None).is_authenticated:
        actor = request.user

    object_type = ""
    object_id = ""
    if obj is not None:
        object_type = obj.__class__.__name__
        object_id = str(getattr(obj, "pk", ""))

    try:
        event = AuditEvent.objects.create(
            actor=actor if isinstance(actor, User) else None,
            event_type=event_type,
            object_type=object_type,
            object_id=object_id,
            request_id=getattr(request, "request_id", "") if request is not None else "",
            ip_address=get_client_ip(request) if request is not None else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000] if request is not None else "",
            metadata=metadata or {},
        )
        logger.info("audit_event", extra={"event_type": event_type, "audit_event_id": event.pk})
        return event
    except Exception:
        logger.exception("audit_event_failed", extra={"event_type": event_type})
        return None
