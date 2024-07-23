# -*- coding: utf-8 -*-

# receiving/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('fetch-emails/', views.fetch_emails, name='fetch_emails'),
    path('received-emails/', views.get_received_emails, name='received_emails'),
    path('received-emails/<int:email_id>/', views.get_email_detail, name='email_detail'),
]