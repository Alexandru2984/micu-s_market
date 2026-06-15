"""La crearea unui mesaj nou, împinge numărul de necitite către destinatar pe
WebSocket (badge live). Best-effort: o eroare de channel layer nu trebuie să
afecteze salvarea mesajului."""
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
