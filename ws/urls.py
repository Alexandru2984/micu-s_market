from django.urls import path
from .views import notifications_stream_view
from .views import chat_room_view

urlpatterns = [

	path("chat_room", chat_room_view),
	path("notifications_stream", notifications_stream_view),
]
