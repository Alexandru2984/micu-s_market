from django.urls import path

from .views import about_view, contact_view, healthcheck_view, home_view, privacy_view, terms_view

urlpatterns = [

	path("healthz", healthcheck_view, name="healthcheck"),
	path("home", home_view, name="home"),
	path("about", about_view, name="about"),
	path("contact", contact_view, name="contact"),
	path("terms", terms_view, name="terms"),
	path("privacy", privacy_view, name="privacy"),
]
