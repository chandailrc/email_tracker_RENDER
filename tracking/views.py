# tracking/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse, HttpResponse
from django.conf import settings
from .models import TrackingLog, LinkClick
from sending.models import Email, Link, TrackingPixelToken
from .serializers import TrackingLogSerializer, LinkClickSerializer, EmailSerializer
from django.utils import timezone
from datetime import timedelta
import os
import uuid
import geoip2.database
import threading
import logging

logger = logging.getLogger(__name__)

class TrackingViewSet(viewsets.ModelViewSet):
    queryset = TrackingLog.objects.all()
    serializer_class = TrackingLogSerializer

    @action(detail=False, methods=['get'])
    def serve_image(self, request, image_name):
        image_path = os.path.join(settings.BASE_DIR, 'static/images', image_name)
        if os.path.exists(image_path):
            response = FileResponse(open(image_path, 'rb'), content_type="image/png")
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Cache-Buster'] = uuid.uuid4().hex
            return response
        else:
            return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def tracking_pixel(self, request, token):
        return self.handle_tracking(request, token, is_pixel=True)

    @action(detail=False, methods=['get'])
    def tracking_css(self, request, token):
        return self.handle_tracking(request, token, is_pixel=False)

    def handle_tracking(self, request, token, is_pixel):
        try:
            logger.info(f"'handle_tracking' called! Process ID: {os.getpid()}, Thread ID: {threading.get_ident()}")
            pixel_token = TrackingPixelToken.objects.get(token=token)
            recipient = pixel_token.email.recipient
            email_id = pixel_token.email.id
            mail = pixel_token.email
            curr_time = timezone.now()

            time_difference = curr_time - mail.sent_at

            if time_difference <= timedelta(seconds=4):
                logger.warning(f"views.py/handle_tracking: First request received for {recipient} with email_id {email_id} within 5 secs. Potential prefetching. Abandoning request!")
                return Response("Not found", status=status.HTTP_404_NOT_FOUND)

            last_log = TrackingLog.objects.filter(email=mail).order_by('-opened_at').first()

            if last_log:
                time_diff = curr_time - last_log.opened_at
                if time_diff <= timedelta(seconds=3):
                    logger.warning(f"views.py/handle_tracking: Request received for {recipient} with email_id {email_id} within 4 secs. Random fetching. Abandoning request!")
                    return Response("Not found", status=status.HTTP_404_NOT_FOUND)

            tracking_data = {
                'email': pixel_token.email.id,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'opened_at': timezone.now(),
                'tracking_type': 'pixel' if is_pixel else 'css',
                'geo_location': self.get_geo_location(self.get_client_ip(request)),
                'referer': request.META.get('HTTP_REFERER', ''),
                'device_type': self.get_device_type(request.META.get('HTTP_USER_AGENT')),
                'screen_resolution': request.META.get('HTTP_UA_PIXELS', ''),
                'language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                'protocol': request.scheme,
                'method': request.method,
                'host': request.get_host(),
                'connection': request.META.get('HTTP_CONNECTION', '')
            }

            serializer = self.get_serializer(data=tracking_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            if is_pixel:
                png_path = os.path.join(settings.BASE_DIR, 'static/images', 'transparent.png')
                response = FileResponse(open(png_path, 'rb'), content_type="image/png")
            else:
                response = HttpResponse(content_type="text/css")
                response.write("")

            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Cache-Buster'] = uuid.uuid4().hex

            return response

        except TrackingPixelToken.DoesNotExist:
            return Response("Not found", status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def get_geo_location(ip_address):
        try:
            reader = geoip2.database.Reader('/path/to/GeoLite2-City.mmdb')
            response = reader.city(ip_address)
            return f"{response.city.name}, {response.subdivisions.most_specific.name}, {response.country.name}"
        except Exception as e:
            return f"Unknown exception {e}"

    @staticmethod
    def get_device_type(user_agent):
        if 'Mobi' in user_agent:
            return 'Mobile'
        elif 'Tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'

class LinkClickViewSet(viewsets.ModelViewSet):
    queryset = LinkClick.objects.all()
    serializer_class = LinkClickSerializer

    @action(detail=False, methods=['get'])
    def track_link(self, request, link_id):
        link = get_object_or_404(Link, pk=link_id)
        
        click_data = {
            'link': link.id,
            'clicked_at': timezone.now(),
            'ip_address': TrackingViewSet.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'geo_location': TrackingViewSet.get_geo_location(TrackingViewSet.get_client_ip(request)),
            'referer': request.META.get('HTTP_REFERER', ''),
            'device_type': TrackingViewSet.get_device_type(request.META.get('HTTP_USER_AGENT')),
            'screen_resolution': request.META.get('HTTP_UA_PIXELS', ''),
            'language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'protocol': request.scheme,
            'method': request.method,
            'host': request.get_host(),
            'connection': request.META.get('HTTP_CONNECTION', '')
        }
        
        serializer = self.get_serializer(data=click_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return redirect(link.url)

class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        emails = Email.objects.all()
        email_serializer = EmailSerializer(emails, many=True)
        
        # Fetch unsubscribed emails
        from unsubscribers.models import UnsubscribedUser
        unsubscribed_emails = UnsubscribedUser.objects.values_list('email', flat=True)
        
        return Response({
            'emails': email_serializer.data,
            'unsubscribed_emails': list(unsubscribed_emails)
        })

    @action(detail=False, methods=['get'])
    def email_detail_data(self, request):
        email_id = request.query_params.get('email_id')
        email = get_object_or_404(Email, pk=email_id)
        
        tracking_logs = TrackingLog.objects.filter(email=email).order_by('-opened_at')
        link_clicks = LinkClick.objects.filter(link__email=email).order_by('-clicked_at')
        
        email_serializer = EmailSerializer(email)
        tracking_logs_serializer = TrackingLogSerializer(tracking_logs, many=True)
        link_clicks_serializer = LinkClickSerializer(link_clicks, many=True)
        
        return Response({
            'email': email_serializer.data,
            'tracking_logs': tracking_logs_serializer.data,
            'link_clicks': link_clicks_serializer.data
        })

    @action(detail=False, methods=['post'])
    def delete_unsubscribed_users(self, request):
        from unsubscribers.models import UnsubscribedUser
        UnsubscribedUser.objects.all().delete()
        return Response({"message": "All unsubscribed users have been deleted."})

    @action(detail=False, methods=['post'])
    def empty_database(self, request):
        Email.objects.all().delete()
        TrackingLog.objects.all().delete()
        Link.objects.all().delete()
        LinkClick.objects.all().delete()
        return Response({"message": "Database has been emptied."})