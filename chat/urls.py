from django.urls import path
from .views import new_message_view
from .views import thread_view
from .views import inbox_view

urlpatterns = [

	path("inbox", inbox_view),
	path("thread", thread_view),
	path("new_message", new_message_view),
]
