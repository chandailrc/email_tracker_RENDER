# -*- coding: utf-8 -*-

from django.urls import path
from . import views

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UnsubscribedUserViewSet

router = DefaultRouter()
router.register(r'users', UnsubscribedUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('delete-unsub-user/', UnsubscribedUserViewSet.as_view({'post': 'delete_unsub_user'}), name='delete_unsub_user'),
]


# urlpatterns = [
#     path('unsubscribe-action/', views.unsubscribe_action, name='unsubscribe_action'),
#     path('unsubscribed-users-data/', views.unsubscribed_users_data, name='unsubscribed_users_data'),
#     path('delete-unsub-user/', views.delete_unsub_user, name='delete_unsub_user'),
# ]