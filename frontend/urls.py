# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('compose/', views.compose_email_view, name='compose_email'),
    path('send-tracked-email/', views.send_tracked_email_view, name='send_tracked_email_view'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('email/<int:email_id>/', views.email_detail, name='email_detail'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('unsubscribed-users/', views.unsubscribed_users_list, name='unsubscribed_users_list'),
    path('delete-unsubscribed-user/<str:user_email>/', views.delete_unsubscribed_user, name='delete_unsubscribed_user'),
]