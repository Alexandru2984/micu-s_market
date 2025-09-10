from django.urls import path
from .views import verify_listings_view
from .views import reports_list_view
from .views import dashboard_home_view

urlpatterns = [

	path("dashboard_home", dashboard_home_view),
	path("reports_list", reports_list_view),
	path("verify_listings", verify_listings_view),
]
