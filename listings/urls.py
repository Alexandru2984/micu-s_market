from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('anunturi/', views.listing_list_view, name='list'),
    path('anunt/<slug:slug>/', views.listing_detail_view, name='detail'),
    path('adauga/', views.listing_create_view, name='create'),
    path('anunt/<slug:slug>/editeaza/', views.listing_update_view, name='update'),
    path('anunt/<slug:slug>/sterge/', views.listing_delete_view, name='delete'),
    path('anunturile-mele/', views.my_listings_view, name='my_listings'),
    path('anunt/<slug:slug>/imagini/', views.upload_images_view, name='upload_images'),
]
