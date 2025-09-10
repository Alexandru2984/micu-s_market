from django.urls import path
from .views import api_create_listing_view
from .views import api_listing_detail_view
from .views import api_listing_list_view

urlpatterns = [

	path("api_listing_list", api_listing_list_view),
	path("api_listing_detail", api_listing_detail_view),
	path("api_create_listing", api_create_listing_view),
]
