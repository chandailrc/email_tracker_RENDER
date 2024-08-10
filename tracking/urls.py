# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('track/<str:encoded_item_id>/', views.track_item, name='track_item'),
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('email-detail-data/', views.email_detail_data, name='email_detail_data'),
    path('delete-unsubscribed-users/', views.delete_unsubscribed_users, name='delete_unsubscribed_users'),
    path('empty-database/', views.empty_database, name='empty_database'),
]