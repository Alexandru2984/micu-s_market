from django.urls import path
from .views import toggle_favorite_view
from .views import favorites_list_view

urlpatterns = [

	path("favorites_list", favorites_list_view),
	path("toggle_favorite", toggle_favorite_view),
]
