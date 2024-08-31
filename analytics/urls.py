from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsViewSet, analytics_form_view

router = DefaultRouter()
router.register(r'', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('form/', analytics_form_view, name='analytics_form'),  # New URL for the form
]