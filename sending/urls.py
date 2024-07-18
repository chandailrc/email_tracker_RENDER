# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('send-tracked-email/', views.send_tracked_email, name='send_tracked_email'),
]
