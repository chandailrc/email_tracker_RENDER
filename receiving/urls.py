from django.urls import path
from . import views

urlpatterns = [
    path('receive/', views.receive_email, name='receive_email'),
    path('fetch/', views.fetch_emails, name='fetch_emails'),
    path('list/', views.list_emails, name='list_emails'),
]