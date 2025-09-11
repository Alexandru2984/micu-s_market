from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.favorites_list_view, name='list'),
    path('toggle/', views.toggle_favorite_view, name='toggle'),
    path('remove/<int:favorite_id>/', views.remove_favorite_view, name='remove'),
]
