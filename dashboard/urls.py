from django.urls import path

from .views import dashboard_home_view, reports_list_view, seller_insights_view, verify_listings_view

app_name = "dashboard"

urlpatterns = [

	path("dashboard_home", dashboard_home_view),
	path("reports_list", reports_list_view),
	path("verify_listings", verify_listings_view),
	path("seller/", seller_insights_view, name="seller_insights"),
]
