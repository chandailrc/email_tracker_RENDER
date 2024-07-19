# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('unsubscribe-action/', views.unsubscribe_action, name='unsubscribe_action'),
    path('unsubscribed-users-data/', views.unsubscribed_users_data, name='unsubscribed_users_data'),
    path('delete-unsub-user/', views.delete_unsub_user, name='delete_unsub_user'),
]