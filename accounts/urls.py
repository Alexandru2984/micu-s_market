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
    path('profile/verification/request/', views.request_verification_view, name='request_verification'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    path('profile/<str:username>/report/', views.report_user_view, name='report_user'),
    # Redirect to the canonical view in the listings app
    path('my-listings/', RedirectView.as_view(pattern_name='listings:my_listings', permanent=True), name='my_listings'),
]
