from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review-uri pentru un utilizator
    path('user/<str:username>/', views.user_reviews_view, name='user_reviews'),
    
    # Creează review
    path('create/<str:username>/', views.create_review_view, name='create_review'),
    path('create/<str:username>/<slug:listing_slug>/', views.create_review_view, name='create_review_listing'),
    
    # Editează și șterge review
    path('edit/<int:review_id>/', views.edit_review_view, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review_view, name='delete_review'),
    
    # Răspuns la review
    path('response/<int:review_id>/', views.add_response_view, name='add_response'),
    
    # Review-urile mele
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
    
    # API
    path('api/stats/<str:username>/', views.reviews_stats_api, name='stats_api'),
]
