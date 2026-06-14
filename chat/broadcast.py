"""Publicare mesaje pe channel layer — folosit atât de consumer (WS), cât și de
view-ul de fallback/atașamente, ca să existe o singură formă serializată."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def conversation_group(conversation_id):
    return f"chat_{conversation_id}"


def serialize_message(message):
    """Reprezentarea JSON a unui mesaj trimisă către clienți (identică pe WS și POST)."""
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
    """Trimite un mesaj (deja salvat) către grupul conversației. Sincron — apelabil
    din view-uri obișnuite. No-op dacă nu există channel layer configurat."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        conversation_group(message.conversation_id),
        {"type": "chat.message", "message": serialize_message(message)},
    )
