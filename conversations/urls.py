from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_conversations, name='list_conversations'),
    path('<int:conversation_id>/', views.get_conversation, name='get_conversation'),
    path('create/', views.create_conversation, name='create_conversation'),
    path('<int:conversation_id>/add_message/', views.add_message_to_conversation, name='add_message_to_conversation'),
    path('update_unread/<int:conversation_id>/', views.update_conversation_unread_status, name='update_conversation_unread_status'),
    path('fetch_unread_id_list/', views.fetch_unread_id_list, name='fetch_unread_id_list'),
]