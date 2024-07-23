# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrackingViewSet, LinkClickViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'tracking', TrackingViewSet)
router.register(r'link-clicks', LinkClickViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('serve-image/<str:image_name>/', TrackingViewSet.as_view({'get': 'serve_image'}), name='serve_image'),
    path('track-pixel/<str:token>/pixel.png', TrackingViewSet.as_view({'get': 'tracking_pixel'}), name='tracking_pixel'),
    path('track-pixel/<str:token>/style.css', TrackingViewSet.as_view({'get': 'tracking_css'}), name='tracking_css'),
    path('track-link/<int:link_id>/', LinkClickViewSet.as_view({'get': 'track_link'}), name='track_link'),
    path('dashboard-data/', DashboardViewSet.as_view({'get': 'dashboard_data'}), name='dashboard_data'),
    path('email-detail-data/', DashboardViewSet.as_view({'get': 'email_detail_data'}), name='email_detail_data'),
    path('delete-unsubscribed-users/', DashboardViewSet.as_view({'post': 'delete_unsubscribed_users'}), name='delete_unsubscribed_users'),
    path('empty-database/', DashboardViewSet.as_view({'post': 'empty_database'}), name='empty_database'),
]