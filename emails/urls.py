# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('email_list/', views.email_list, name='email_list'),
]
