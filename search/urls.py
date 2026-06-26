from django.urls import path
from . import views

app_name = "search"

urlpatterns = [
	path("search", views.search_view, name="search"),
	path("advanced_search", views.advanced_search_view, name="advanced_search"),
	path("saved_searches", views.saved_searches_view, name="saved_searches"),
	path("saved_searches/<int:pk>/run/", views.run_saved_search_view, name="run_saved_search"),
	path("saved_searches/<int:pk>/toggle/", views.toggle_saved_search_view, name="toggle_saved_search"),
	path("saved_searches/<int:pk>/delete/", views.delete_saved_search_view, name="delete_saved_search"),
]
