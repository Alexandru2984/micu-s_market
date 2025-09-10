from django.urls import path
from .views import privacy_view
from .views import terms_view
from .views import contact_view
from .views import about_view
from .views import home_view

urlpatterns = [

	path("home", home_view),
	path("about", about_view),
	path("contact", contact_view),
	path("terms", terms_view),
	path("privacy", privacy_view),
]
