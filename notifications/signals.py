"""On a new message, push the unread count to the recipient over WebSocket (live
badge). Best-effort: a channel-layer error must not affect saving the message."""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.models import Message
from .consumers import user_group

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message, dispatch_uid="notifications_push_unread")
def push_unread_on_message(sender, instance, created, **kwargs):
    if not created or instance.receiver_id is None:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        count = Message.objects.filter(receiver_id=instance.receiver_id, is_read=False).count()
        async_to_sync(layer.group_send)(
            user_group(instance.receiver_id),
            {"type": "notif.update", "count": count},
        )
    except Exception:
        logger.warning("live notification push failed", exc_info=True)
