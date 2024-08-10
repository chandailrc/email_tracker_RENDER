# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('send-tracked-email/', views.send_tracked_email, name='send_tracked_email'),
    path('serve-image/<str:image_name>/', views.serve_image, name='serve_image'),
]
