from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    # Reviews for a user
    path('user/<str:username>/', views.user_reviews_view, name='user_reviews'),

    # Create review
    path('create/<str:username>/', views.create_review_view, name='create_review'),
    path('create/<str:username>/<slug:listing_slug>/', views.create_review_view, name='create_review_listing'),

    # Edit and delete review
    path('edit/<int:review_id>/', views.edit_review_view, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review_view, name='delete_review'),

    # Response to a review
    path('response/<int:review_id>/', views.add_response_view, name='add_response'),

    # My reviews
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
    
    # API
    path('api/stats/<str:username>/', views.reviews_stats_api, name='stats_api'),
]
