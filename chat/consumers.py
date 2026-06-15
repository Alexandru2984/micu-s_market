"""WebSocket consumer for real-time chat.

Security: the connection is accepted only for an authenticated participant of the
conversation. The Origin is validated in asgi.py (AllowedHostsOriginValidator)."""
import json
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .broadcast import conversation_group, serialize_message

# Minimum interval between two messages on the same connection (anti-spam;
# django-ratelimit does not cover WebSockets).
MIN_MESSAGE_INTERVAL = 0.3


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.conversation_id = int(self.scope["url_route"]["kwargs"]["pk"])
        self._last_message_ts = 0.0

        if self.user is None or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        if not await self._is_participant():
            await self.close(code=4403)
            return

        self.group = conversation_group(self.conversation_id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # On open, mark as read and notify the other side (read receipts).
        await self._mark_read()
        await self.channel_layer.group_send(self.group, {"type": "chat.read", "by": self.user.id})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")
        if msg_type == "message":
            await self._handle_message(data)
        elif msg_type == "typing":
            await self.channel_layer.group_send(self.group, {"type": "chat.typing", "user_id": self.user.id})
        elif msg_type == "read":
            await self._mark_read()
            await self.channel_layer.group_send(self.group, {"type": "chat.read", "by": self.user.id})

    async def _handle_message(self, data):
        content = (data.get("content") or "").strip()
        if not content:
            return
        if len(content) > settings.CHAT_MESSAGE_MAX_LENGTH:
            content = content[: settings.CHAT_MESSAGE_MAX_LENGTH]

        now = time.monotonic()
        if now - self._last_message_ts < MIN_MESSAGE_INTERVAL:
            return
        self._last_message_ts = now

        message = await self._save_message(content)
        payload = await self._serialize(message)
        await self.channel_layer.group_send(self.group, {"type": "chat.message", "message": payload})

    # --- group handlers -> client ---
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type": "message", "message": event["message"]}))

    async def chat_typing(self, event):
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps({"type": "typing", "user_id": event["user_id"]}))

    async def chat_read(self, event):
        if event["by"] != self.user.id:
            await self.send(text_data=json.dumps({"type": "read", "by": event["by"]}))

    # --- DB access ---
    @database_sync_to_async
    def _is_participant(self):
        from .models import Conversation
        return Conversation.objects.filter(pk=self.conversation_id, participants=self.user).exists()

    @database_sync_to_async
    def _save_message(self, content):
        from .models import Conversation, Message
        from notifications.models import Notification

        conversation = Conversation.objects.get(pk=self.conversation_id)
        receiver = conversation.get_other_participant(self.user)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            receiver=receiver,
            content=content,
        )
        if receiver is not None:
            Notification.objects.create(
                recipient=receiver,
                notification_type="new_message",
                title="Mesaj nou",
                message=f"{self.user.get_full_name() or self.user.username} ți-a trimis un mesaj.",
                related_object_type="Conversation",
                related_object_id=conversation.pk,
                action_url=conversation.get_absolute_url(),
            )
        return message

    @database_sync_to_async
    def _serialize(self, message):
        return serialize_message(message)

    @database_sync_to_async
    def _mark_read(self):
        from .models import Conversation
        Conversation.objects.get(pk=self.conversation_id).mark_as_read(self.user)
