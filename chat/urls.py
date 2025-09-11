from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Inbox principal
    path('', views.inbox_view, name='inbox'),
    
    # Conversații
    path('conversation/<int:pk>/', views.conversation_view, name='conversation'),
    path('start/<slug:listing_slug>/', views.start_conversation_view, name='start_conversation'),
    
    # Acțiuni AJAX
    path('send/<int:conversation_pk>/', views.send_message_view, name='send_message'),
    path('mark-read/<int:pk>/', views.mark_conversation_read, name='mark_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('search-users/', views.search_users_view, name='search_users'),
]
