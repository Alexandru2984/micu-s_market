"""WebSocket consumer for the real-time notification/message badge.

Each authenticated user joins the ``notifications_<id>`` group; the signal in
notifications/signals.py pushes the unread message count on every new message,
so the badge updates instantly without polling."""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


def user_group(user_id):
    return f"notifications_{user_id}"


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if self.user is None or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.group = user_group(self.user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        # Send the current count on connect (badge correct immediately on load).
        await self.send(text_data=json.dumps({"type": "unread", "count": await self._unread()}))

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notif_update(self, event):
        await self.send(text_data=json.dumps({"type": "unread", "count": event["count"]}))

    @database_sync_to_async
    def _unread(self):
        from chat.models import Message
        return Message.objects.filter(receiver=self.user, is_read=False).count()
