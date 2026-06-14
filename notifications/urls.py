from django.urls import path
from .views import mark_read_view
from .views import notifications_list_view

app_name = "notifications"

urlpatterns = [
	path("notifications_list", notifications_list_view, name="list"),
	path("mark_read", mark_read_view, name="mark_read"),
]
