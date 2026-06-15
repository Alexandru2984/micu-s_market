"""Publish messages to the channel layer — used by both the consumer (WS) and the
fallback/attachment view, so there is a single serialized form."""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def conversation_group(conversation_id):
    return f"chat_{conversation_id}"


def serialize_message(message):
    """JSON representation of a message sent to clients (identical over WS and POST)."""
    return {
        "id": message.id,
        "content": message.content,
        "sender": message.sender.username,
        "sender_id": message.sender_id,
        "created_at": message.created_at.strftime("%H:%M"),
        "attachments": [
            {
                "download_url": att.download_url,
                "filename": att.filename,
                "file_type": att.file_type,
            }
            for att in message.attachments.all()
        ],
    }


def broadcast_message(message):
    """Send an already-saved message to the conversation group. Synchronous — callable
    from regular views. Best-effort: the message is already persisted, so a channel
    layer error (e.g. Redis unavailable) must not break the HTTP request."""
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            conversation_group(message.conversation_id),
            {"type": "chat.message", "message": serialize_message(message)},
        )
    except Exception:
        logger.warning("chat broadcast failed for message %s", message.pk, exc_info=True)
