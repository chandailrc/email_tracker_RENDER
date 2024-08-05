# -*- coding: utf-8 -*-

from django.urls import path
from . import views
import logging
from sending.models import TrackingPixelToken, Link

logger = logging.getLogger(__name__)

def log_request_pixel(view_func):
    def wrapper(request, token, *args, **kwargs):
        try:
            recipient = TrackingPixelToken.objects.get(token=token).email.recipient
            logger.info(f"urls.py: PIXEL Request received for email {recipient} from ip: {views.get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: PIXEL Request received with invalid token {token} from ip: {views.get_client_ip(request)}")
        return view_func(request, token, *args, **kwargs)
    return wrapper

def log_request_css(view_func):
    def wrapper(request, token, *args, **kwargs):
        try:
            recipient = TrackingPixelToken.objects.get(token=token).email.recipient
            logger.info(f"urls.py: CSS Request received for email {recipient} from ip: {views.get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: CSS Request received with invalid token {token} from ip: {views.get_client_ip(request)}")
        return view_func(request, token, *args, **kwargs)
    return wrapper

def log_request_link(view_func):
    def wrapper(request, link_id, *args, **kwargs):
        try:
            recipient = Link.objects.get(id=link_id).email.recipient
            logger.info(f"urls.py: LINK Request received for email {recipient} from ip: {views.get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: LINK Request received with invalid link_id {link_id} from ip: {views.get_client_ip(request)}")
        return view_func(request, link_id, *args, **kwargs)
    return wrapper

urlpatterns = [
    path('serve-image/<str:image_name>/', views.serve_image, name='serve_image'),
    path('track-pixel/<str:token>/', log_request_pixel(views.tracking_pixel), name='tracking_pixel'),
    # path('track-pixel/<str:token>/ss', log_request_css(views.tracking_css), name='tracking_css'),
    path('track-link/<int:link_id>/', log_request_link(views.track_link), name='track_link'),
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('email-detail-data/', views.email_detail_data, name='email_detail_data'),
    path('delete-unsubscribed-users/', views.delete_unsubscribed_users, name='delete_unsubscribed_users'),
    path('empty-database/', views.empty_database, name='empty_database'),
]