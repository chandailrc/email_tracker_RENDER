from django.http import HttpResponse, FileResponse
from django.utils import timezone
from .models import TrackingLog, TrackingPixelToken
from django.shortcuts import render
from .email_utils import send_tracked_email
from django.shortcuts import get_object_or_404, redirect
from .models import Link, LinkClick
import time
from .models import Email, UnsubscribedUser
from datetime import datetime, timedelta
import random
import os
from django.conf import settings
import uuid


import logging

logger = logging.getLogger(__name__)

import base64

from .mailgun_utils import send_email, send_simple_message

import geoip2.database

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_geo_location(ip_address):
    try:
        reader = geoip2.database.Reader('/path/to/GeoLite2-City.mmdb')
        response = reader.city(ip_address)
        return f"{response.city.name}, {response.subdivisions.most_specific.name}, {response.country.name}"
    except Exception as e:
        return "Unknown"

def get_device_type(user_agent):
    if 'Mobi' in user_agent:
        return 'Mobile'
    elif 'Tablet' in user_agent:
        return 'Tablet'
    else:
        return 'Desktop'

def send_mailgun_mail_view(request):
    subject = "Hello from Mailgun 2"
    message = "This is a test email sent via Mailgun. Link --> https://www.google.com"
    html_text = "<html><body><p>This is the HTML version</p></body></html>"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [
                    "mukulchandail@gmail.com",
                    "mukulchandail@yahoo.com",
                    "1chandailrc1@gmail.com",
                    "chandailrc@gmail.com",
                    "chandailrc@hotmail.com",
                    "singhal1959a@gmail.com",
                    "singhal24a@gmail.com",
                    "chandailrcsai@gmail.com",
                    "chandailrcsai@outlook.com",
                    "spamtestsai@outlook.com",
                    "dpo0qnhg@temporary-mail.net",
                    "bucofomopudi@gotgel.org",
                    "ines850@magicth.com",
                    "lamoruze@pelagius.net",
                    "afoweitbf@10mail.org",
                    "jixamo8511@carspure.com",
                    "spamtestersai@maildrop.cc",
                    "mtkzvf@vobau.net"
                    ]
    for recip in recipient_list[2:3]:
        response = send_email(subject, message, from_email, recip, html_text)
        # response = send_simple_message(subject, message, from_email, recip)
    
    if response.status_code == 200:
        return HttpResponse("Email sent successfully!")
    else:
        return HttpResponse(f"Failed to send email. Status code: {response.status_code}")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Take the first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def tracking_pixel(request, token):
    recipient = TrackingPixelToken.objects.get(token=token).email.recipient
    # logger.info(f"views.py/PIXEL: Request received for {recipient} from {get_client_ip(request)}.")
    return handle_tracking(request, token, is_pixel=True)

def tracking_css(request, token):
    recipient = TrackingPixelToken.objects.get(token=token).email.recipient
    # logger.info(f"views.py/CSS: Request received for {recipient} from {get_client_ip(request)}")
    return handle_tracking(request, token, is_pixel=False)


def handle_tracking(request, token, is_pixel):
    try:
        logger.info(f"'handle_tracking' called! Process ID: {os.getpid()}, Thread ID: {threading.get_ident()}")
        pixel_token = TrackingPixelToken.objects.get(token=token)
        recipient = pixel_token.email.recipient
        email_id = pixel_token.email.id
        mail = pixel_token.email
        curr_time = timezone.now()

        # Calculate the time difference
        time_difference = curr_time - mail.sent_at

        # Compare the difference
        if time_difference <= timedelta(seconds=4):
            logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {mail.sent_at} | Difference: {time_difference}")
            logger.warning(f"views.py/handle_tracking: First request received for {recipient} with email_id {email_id} within 5 secs. Potential prefetching. Abandoning request!")
            return HttpResponse("Not found", status=404)
        else:
            logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {mail.sent_at} | Difference: {time_difference}")
            # Retrieve the most recent TrackingLog for this email
            last_log = TrackingLog.objects.filter(email=mail).order_by('-opened_at').first()

            if last_log:
                time_diff = curr_time - last_log.opened_at

                if time_diff <= timedelta(seconds=3):
                    logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.opened_at} | Difference: {time_diff}")
                    logger.warning(f"views.py/handle_tracking: Request received for for {recipient} with email_id {email_id} within 4 secs. Random fetching. Abandoning request!")
                    return HttpResponse("Not found", status=404)
                else:
                    logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.opened_at} | Difference: {time_diff}")
                    print("Greater than 4 seconds since the last log")
            else:
                print("No previous logs found")

            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT')
            geo_location = get_geo_location(ip_address)
            device_type = get_device_type(user_agent)
            referer = request.META.get('HTTP_REFERER', '')
            screen_resolution = request.META.get('HTTP_UA_PIXELS', '')
            language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            protocol = request.scheme
            method = request.method
            host = request.get_host()
            connection = request.META.get('HTTP_CONNECTION', '')

            TrackingLog.objects.create(
                email=pixel_token.email,
                ip_address=ip_address,
                user_agent=user_agent,
                opened_at=timezone.now(),
                tracking_type='pixel' if is_pixel else 'css',
                geo_location=geo_location,
                referer=referer,
                device_type=device_type,
                screen_resolution=screen_resolution,
                language=language,
                protocol=protocol,
                method=method,
                host=host,
                connection=connection
            )

            if is_pixel:
                # Serve a 1x1 transparent PNG
                # As file:
                png_path = os.path.join(settings.BASE_DIR, 'static/images', 'transparent.png')

                response = FileResponse(open(png_path, 'rb'), content_type="image/png")
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max_age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                response['Cache-Buster'] = uuid.uuid4().hex  # Custom header

                return response
            else:
                # As hardcoded data
                css_data = ""

                # Serve an empty CSS file
                response = HttpResponse(content_type="text/css")
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                response['Cache-Buster'] = uuid.uuid4().hex  # Custom header
                response.write(css_data)
                return response

    except TrackingPixelToken.DoesNotExist:
        return HttpResponse("Not found", status=404)

def serve_image(request, image_name):
    image_path = os.path.join(settings.BASE_DIR, 'static/images', image_name)
    if os.path.exists(image_path):
        response = FileResponse(open(image_path, 'rb'), content_type="image/png")
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max_age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['Cache-Buster'] = uuid.uuid4().hex  # Custom header

        return response#FileResponse(open(image_path, 'rb'), content_type='image/png')
    else:
        return HttpResponse('Image not found.', status=404)

from django.urls import reverse
def empty_database(request):
    # Ensure that only POST requests can trigger this action (for safety)
    if request.method == 'POST':
        # Delete all records from all relevant models
        Email.objects.all().delete()
        TrackingLog.objects.all().delete()
        Link.objects.all().delete()
        LinkClick.objects.all().delete()        
        # Redirect to a success page or back to the dashboard
        return redirect(reverse('dashboard'))  # Adjust 'dashboard' to your actual dashboard URL name

def delete_unsubscribed_users(request):
    if request.method == 'POST':
        UnsubscribedUser.objects.all().delete()
        return redirect('unsubscribed_users_list')

def track_link(request, link_id):
    link = get_object_or_404(Link, pk=link_id)
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT')
    geo_location = get_geo_location(ip_address)
    device_type = get_device_type(user_agent)
    referer = request.META.get('HTTP_REFERER', '')
    screen_resolution = request.META.get('HTTP_UA_PIXELS', '')
    language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    protocol = request.scheme
    method = request.method
    host = request.get_host()
    connection = request.META.get('HTTP_CONNECTION', '')

    LinkClick.objects.create(
        link=link,
        clicked_at=datetime.now(),
        ip_address=ip_address,
        user_agent=user_agent,
        geo_location=geo_location,
        referer=referer,
        device_type=device_type,
        screen_resolution=screen_resolution,
        language=language,
        protocol=protocol,
        method=method,
        host=host,
        connection=connection
    )
    
    return redirect(link.url)

def dashboard(request):
    emails = Email.objects.all()
    unsubscribed_users = UnsubscribedUser.objects.values_list('email', flat=True)
    return render(request, 'dashboard.html', {'emails': emails, 'unsubscribed_emails': unsubscribed_users})

def unsubscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            UnsubscribedUser.objects.get_or_create(email=email)
            return HttpResponse('You have been unsubscribed.')
    return render(request, 'unsubscribe.html')


def unsubscribed_users_list(request):
    unsubscribed_users = UnsubscribedUser.objects.values_list('email', flat=True)
    return render(request, 'unsubscribed_users_list.html', {'unsubscribed_emails': unsubscribed_users})

def compose_email_view(request):
    return render(request, 'compose_email.html')

import threading

def send_tracked_email_view(request):
    if request.method == 'POST':
        recipients = request.POST.get('recipients').split()  # Split on whitespace
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        delay_type = request.POST.get('delay_type')
        delay_value = int(request.POST.get('delay_value', 0))
        min_delay = int(request.POST.get('min_delay', 0))
        max_delay = int(request.POST.get('max_delay', 0))

        sent_count = 0
        for recipient in recipients:
            recipient = recipient.strip()
            if recipient:
                logger.info(f"Sending email to {recipient}. Process ID: {os.getpid()}, Thread ID: {threading.get_ident()}")
                success = send_tracked_email(recipient, subject, body)
                if success:
                    sent_count += 1
                    print(f"views.py/send_tracked_email_view: Email sent successfully to {recipient}")
                else:
                    print(f"views.py/send_tracked_email_view: Failed to send email to {recipient}")

                if delay_type == 'fixed':
                    time.sleep(delay_value)
                elif delay_type == 'random':
                    time.sleep(random.uniform(min_delay, max_delay))

        confirmation_message = f"{sent_count} email(s) sent successfully!"
        print(confirmation_message)  # Add this line for debugging
        return render(request, 'compose_email.html', {'confirmation_message': confirmation_message})

    return render(request, 'compose_email.html')

from django.shortcuts import render, get_object_or_404
from .models import Email, TrackingLog, LinkClick

def email_detail(request, email_id):
    email = get_object_or_404(Email, pk=email_id)
    tracking_logs = TrackingLog.objects.filter(email=email).order_by('-opened_at')
    link_clicks = LinkClick.objects.filter(link__email=email).order_by('-clicked_at')

    context = {
        'email': email,
        'tracking_logs': tracking_logs,
        'link_clicks': link_clicks,
    }

    return render(request, 'email_detail.html', context)
