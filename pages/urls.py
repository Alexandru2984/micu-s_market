from django.urls import path
from .views import healthcheck_view
from .views import privacy_view
from .views import terms_view
from .views import contact_view
from .views import about_view
from .views import home_view

urlpatterns = [

	path("healthz", healthcheck_view, name="healthcheck"),
	path("home", home_view, name="home"),
	path("about", about_view, name="about"),
	path("contact", contact_view, name="contact"),
	path("terms", terms_view, name="terms"),
	path("privacy", privacy_view, name="privacy"),
]
