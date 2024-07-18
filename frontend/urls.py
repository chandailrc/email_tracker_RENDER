# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('compose/', views.compose_email_view, name='compose_email'),
    path('send-tracked-email/', views.send_tracked_email_view, name='send_tracked_email_view'),
]