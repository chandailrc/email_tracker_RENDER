import os
import uuid
import geoip2.database

from .models import TrackingItem, TrackingEvent, EmailInteraction
from .tracking_utils import aggregate_genuine_opens
from datetime import timedelta
from django.http import HttpResponse, FileResponse, JsonResponse, Http404
from django.core import serializers
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from sending.models import SentEmail
from unsubscribers.models import UnsubscribedUser

import logging

logger = logging.getLogger('django')



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_geo_location(ip_address):
    db_path = os.path.join(settings.BASE_DIR, 'GeoLite2-City.mmdb')
    try:
        reader = geoip2.database.Reader(db_path)
        response = reader.city(ip_address)
        return f"{response.city.name}, {response.subdivisions.most_specific.name}, {response.country.name}"
    except Exception as e:
        return f"Unknown exception {e}"

def get_device_type(user_agent):
    if 'Mobi' in user_agent:
        return 'Mobile'
    elif 'Tablet' in user_agent:
        return 'Tablet'
    else:
        return 'Desktop'


import logging
from .tracking_utils import decode_tracking_id

logger = logging.getLogger(__name__)

def track_item(request, encoded_item_id):
    decoded_id = decode_tracking_id(encoded_item_id)
    if not decoded_id:
        return HttpResponse("Invalid tracking link", status=400)

    try:
        tracking_item = get_object_or_404(TrackingItem, id=decoded_id)
        
        if not tracking_item.is_valid():
            return HttpResponse("Tracking link expired", status=410)
        
        curr_time = timezone.now()
        time_difference = curr_time - tracking_item.email.sent_at
        prefetch_timediff = 3
        multhit_timediff = 2
        
        if tracking_item.item_type == 'PIXEL':
            if time_difference <= timedelta(seconds=prefetch_timediff):
                logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {tracking_item.email.sent_at} | Difference: {time_difference}")
                logger.warning(f"views.py/handle_tracking: First request received for {tracking_item.email.recipient} with email_id {tracking_item.email.id} within {prefetch_timediff} secs. Potential prefetching. Abandoning request!")
                return HttpResponse("Not found", status=404)
            else:
                logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {tracking_item.email.sent_at} | Difference: {time_difference}")
                # Retrieve the most recent TrackingLog for this email
                last_log = TrackingEvent.objects.filter(tracking_item=tracking_item).order_by('-timestamp').first()
                if last_log:
                    time_diff = curr_time - last_log.timestamp
    
                    if time_diff <= timedelta(seconds=multhit_timediff):
                        logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.timestamp} | Difference: {time_diff}")
                        logger.warning(f"views.py/handle_tracking: Request received for for {tracking_item.email.recipient} with email_id {tracking_item.email.id} within {multhit_timediff} secs. Random fetching. Abandoning request!")
                        return HttpResponse("Not found", status=404)
                    else:
                        logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.timestamp} | Difference: {time_diff}")
                        logger.info(f"Greater than {multhit_timediff} seconds since the last log")
                else:
                    logger.info("No previous logs found")
        
        TrackingEvent.objects.create(
            tracking_item=tracking_item,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            geo_location=get_geo_location(get_client_ip(request)),
            referer=request.META.get('HTTP_REFERER', ''),
            device_type=get_device_type(request.META.get('HTTP_USER_AGENT')),
            screen_resolution=request.META.get('HTTP_UA_PIXELS', ''),
            language=request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            protocol=request.scheme,
            method=request.method,
            host=request.get_host(),
            connection=request.META.get('HTTP_CONNECTION', '')
            )
        
        
        if tracking_item.item_type == 'PIXEL':
            
            EmailInteraction.objects.create(
                email=tracking_item.email,
                interaction_type='open',
                timestamp=timezone.now()
            )
            
            # Serve transparent PNG
            png_path = os.path.join(settings.BASE_DIR, 'static/images', 'transparent.png')
            response = FileResponse(open(png_path, 'rb'), content_type="image/png")
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Cache-Buster'] = uuid.uuid4().hex
            return response
        
        elif tracking_item.item_type == 'LINK':
            
            EmailInteraction.objects.create(
                email=tracking_item.email,
                interaction_type='click',
                timestamp=timezone.now()
            )
            
            return redirect(tracking_item.url)
    
    except TrackingItem.DoesNotExist:
        return HttpResponse("Not found", status=404)

#!!!!!!!!!! DELETE empty_database  and  delete_unsubscribed_users !!!!!!!!!!!
from django.urls import reverse
def empty_database(request):
    if request.method == 'POST':
        SentEmail.objects.all().delete()
        # TrackingLog.objects.all().delete()
        # Link.objects.all().delete()
        # LinkClick.objects.all().delete()        
        return redirect(reverse('dashboard'))

def delete_unsubscribed_users(request):
    if request.method == 'POST':
        UnsubscribedUser.objects.all().delete()
        return redirect('unsubscribed_users_list')

from receiving.models import ReceivedEmail
@csrf_exempt
def dashboard_data(request):
    # Fetch emails sent by the current user
    print(f'username : {request.user.username}')
    emails = SentEmail.objects.filter(user=request.user)
    
    # Fetch unsubscribed users, but only for emails sent by the current user
    unsubscribed_users = UnsubscribedUser.objects.filter(
        email__in=emails.values_list('recipient', flat=True)
    ).values_list('email', flat=True)
    
    # pixel_event_count_list = []
    # for email in emails:
    #     pixel_event_count = TrackingEvent.objects.filter(tracking_item__email=email, tracking_item__item_type='PIXEL').count()
    #     pixel_event_count_list.append(pixel_event_count)
    
    
    # sent_emails = SentEmail.objects.all()
    # received_emails = ReceivedEmail.objects.all()
    
    # print("\n\n >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SENT MAILS")
    
    # for mail in sent_emails:
    #     print("\n\n")
    #     print('<<<<<<<<<<<<<<<<< mail')
    #     print(mail)
    #     print('<<<<<<<<<<<<<<<<< mail.subject')
    #     print(mail.subject)
    #     print('<<<<<<<<<<<<<<<<< mail.body')
    #     print(mail.body)
    #     print('<<<<<<<<<<<<<<<<< mail.id')
    #     print(mail.id)
    #     print('<<<<<<<<<<<<<<<<< mail.message_id')
    #     print(mail.message_id)
    #     print('<<<<<<<<<<<<<<<<< mail.thread_id')
    #     print(mail.thread_id)
    #     print('<<<<<<<<<<<<<<<<< mail.in_reply_to')
    #     print(mail.in_reply_to)
        
    # print("\n\n >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> RECEIVED MAILS")
    # for mail in received_emails:
    #     print("\n\n")
    #     print('<<<<<<<<<<<<<<<<< mail')
    #     print(mail)
    #     print('<<<<<<<<<<<<<<<<< mail.subject')
    #     print(mail.subject)
    #     print('<<<<<<<<<<<<<<<<< mail.body')
    #     print(mail.body)
    #     print('<<<<<<<<<<<<<<<<< mail.id')
    #     print(mail.id)
    #     print('<<<<<<<<<<<<<<<<< mail.message_id')
    #     print(mail.message_id)
    #     print('<<<<<<<<<<<<<<<<< mail.thread_id')
    #     print(mail.thread_id)
    #     print('<<<<<<<<<<<<<<<<< mail.in_reply_to')
    #     print(mail.in_reply_to)
      
    # Serialize the email data
    emails_data = serializers.serialize('json', emails)
    
    # Aggregate genuine opens
    aggregate_genuine_opens(emails)
    
    return JsonResponse({
        'emails': emails_data,
        'unsubscribed_users': list(unsubscribed_users),
        # 'pixel_event_count_list': pixel_event_count_list
    })

def email_detail_data(request):
    email_id = request.GET.get('email_id')
    
    try:
        email = SentEmail.objects.get(pk=email_id, user=request.user)
    except SentEmail.DoesNotExist:
        raise Http404("Email not found or you don't have permission to view it.")
    
    # Get tracking logs (opens)
    pixel_events = TrackingEvent.objects.filter(
        tracking_item__email=email,
        tracking_item__item_type='PIXEL'
    ).order_by('-timestamp')
    
    # Get link clicks
    link_events = TrackingEvent.objects.filter(
        tracking_item__email=email,
        tracking_item__item_type='LINK'
    ).order_by('-timestamp')
    
    email_data = serializers.serialize('json', [email])
    pixel_events_data = serializers.serialize('json', pixel_events)
    link_events_data = serializers.serialize('json', link_events)
    
    return JsonResponse({
        'email': email_data,
        'pixel_events': pixel_events_data,
        'link_events': link_events_data
    })

