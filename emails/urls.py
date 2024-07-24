# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('email_list/', views.email_list, name='email_list'),
    path('api/fetch-emails/', views.fetch_emails, name='fetch_emails'),
    path('api/emails/<int:email_id>/', views.get_email, name='get_email'),
    path('api/emails/<int:email_id>/reply/', views.reply_to_email, name='reply_to_email'),
]