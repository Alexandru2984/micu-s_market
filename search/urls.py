from django.urls import path
from .views import saved_searches_view
from .views import advanced_search_view
from .views import search_view

urlpatterns = [

	path("search", search_view),
	path("advanced_search", advanced_search_view),
	path("saved_searches", saved_searches_view),
]
