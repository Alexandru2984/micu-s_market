from django.urls import path
from .views import mark_read_view
from .views import notifications_list_view

urlpatterns = [

	path("notifications_list", notifications_list_view),
	path("mark_read", mark_read_view),
]
