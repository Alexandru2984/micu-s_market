from django.urls import path

from . import views

urlpatterns = [
    path("listings/", views.listing_list_api, name="listing_list"),
    path("listings/create/", views.listing_create_api, name="listing_create"),
    path("listings/<slug:slug>/", views.listing_detail_api, name="listing_detail"),
    path("favorites/toggle/", views.favorite_toggle_api, name="favorite_toggle"),
]
