# -*- coding: utf-8 -*-

from django.urls import path
from .views import *
import logging
from .models import TrackingPixelToken, Link

logger = logging.getLogger(__name__)

def log_request_pixel(view_func):
    def wrapper(request, token, *args, **kwargs):
        try:
            recipient = TrackingPixelToken.objects.get(token=token).email.recipient
            logger.info(f"urls.py: PIXEL Request received for email {recipient} from ip: {get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: PIXEL Request received with invalid token {token} from ip: {get_client_ip(request)}")
        return view_func(request, token, *args, **kwargs)
    return wrapper

def log_request_css(view_func):
    def wrapper(request, token, *args, **kwargs):
        try:
            recipient = TrackingPixelToken.objects.get(token=token).email.recipient
            logger.info(f"urls.py: CSS Request received for email {recipient} from ip: {get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: CSS Request received with invalid token {token} from ip: {get_client_ip(request)}")
        return view_func(request, token, *args, **kwargs)
    return wrapper

def log_request_link(view_func):
    def wrapper(request, link_id, *args, **kwargs):
        try:
            recipient = Link.objects.get(id=link_id).email.recipient
            logger.info(f"urls.py: LINK Request received for email {recipient} from ip: {get_client_ip(request)}")
        except TrackingPixelToken.DoesNotExist:
            logger.error(f"urls.py: LINK Request received with invalid link_id {link_id} from ip: {get_client_ip(request)}")
        return view_func(request, link_id, *args, **kwargs)
    return wrapper

urlpatterns = [
    path('send-mailgun-mail/', send_mailgun_mail_view, name='mailgun_mail'),
    path('serve-image/<str:image_name>/', serve_image, name='serve_image'),
    path('empty-database/', empty_database, name='empty_database'),
    path('compose/', compose_email_view, name='compose_email'),
    path('send-tracked-email/', send_tracked_email_view, name='send_tracked_email_view'),
    # path('tracking/<int:email_id>/', track_email, name='track_email'),
    path('track/<str:token>/pixel.png', log_request_pixel(tracking_pixel), name='tracking_pixel'),
    path('track/<str:token>/style.css', log_request_css(tracking_css), name='tracking_css'),
    path('dashboard/', dashboard, name='dashboard'),
    path('track-link/<int:link_id>/', log_request_link(track_link), name='track_link'),
    path('unsubscribe/', unsubscribe, name='unsubscribe'),
    path('unsubscribed_users/', unsubscribed_users_list, name='unsubscribed_users_list'),
    path('delete-unsubscribed-users/', delete_unsubscribed_users, name='delete_unsubscribed_users'),
    # path('image/', serve_image, name='serve_image'),

]