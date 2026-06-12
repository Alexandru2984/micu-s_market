# accounts/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "accounts"

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    # Redirectează la view-ul canonic din listings app
    path('my-listings/', RedirectView.as_view(pattern_name='listings:my_listings', permanent=True), name='my_listings'),
]
