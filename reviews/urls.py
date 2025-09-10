from django.urls import path
from .views import create_review
from .views import reviews_for_user_view

urlpatterns = [

	path("reviews_for_user", reviews_for_user_view),
	path("create_review", create_review),
]
