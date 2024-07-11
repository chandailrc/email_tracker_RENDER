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


import logging

logger = logging.getLogger(__name__)

import base64

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
        logger.info(f"View2 called. Process ID: {os.getpid()}, Thread ID: {threading.get_ident()}")
        pixel_token = TrackingPixelToken.objects.get(token=token)
        recipient = pixel_token.email.recipient
        email_id = pixel_token.email.id
        mail = pixel_token.email
        curr_time = timezone.now()

        # Calculate the time difference
        time_difference = curr_time - mail.sent_at

        # Compare the difference
        if time_difference <= timedelta(seconds=5):
            
            logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {mail.sent_at} | Difference: {time_difference}")
            logger.warning(f"views.py/handle_tracking: First request received for {recipient} with email_id {email_id} within 5 secs. Potential prefetching. Abandoning request!")
            
            return HttpResponse("Not found", status=404)
        else:
            logger.info(f"views.py/handle_tracking: PrefetchCheck - Current time: {curr_time} | Mail sent: {mail.sent_at} | Difference: {time_difference}")
            # Retrieve the most recent TrackingLog for this email
            last_log = TrackingLog.objects.filter(email=mail).order_by('-opened_at').first()

            if last_log:
                time_diff = curr_time - last_log.opened_at

                if time_diff <= timedelta(seconds=4):
                    logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.opened_at} | Difference: {time_diff}")
                    logger.warning(f"views.py/handle_tracking: Request received for for {recipient} with email_id {email_id} within 4 secs. Random fetching. Abandoning request!")
                    return HttpResponse("Not found", status=404)
                else:
                    logger.info(f"views.py/handle_tracking: MultihitCheck - Current time: {curr_time} | last_log time: {last_log.opened_at} | Difference: {time_diff}")
                    print("Greater than 4 seconds since the last log")
                    
            else:
                # If there is no previous log, you might want to treat it as case A or B
                # depending on your application logic
                print("No previous logs found")
                # Add your logic here

            TrackingLog.objects.create(
                email=pixel_token.email,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                opened_at=timezone.now(),
                # is_expired_open=pixel_token.is_expired(),
                tracking_type='pixel' if is_pixel else 'css'
            )

            if is_pixel:
                # Serve a 1x1 transparent PNG
                # As file:
                # png_path = os.path.join(settings.BASE_DIR, 'static', 'transparent.png')
                # with open(png_path, 'rb') as png_file:
                #     png_data = png_file.read()

                # As hardcoded data
                png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9c\x63\x60\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'

                # Encode the PNG data to base64
                # base64_png = base64.b64encode(png_data).decode('utf-8')

                # Return a 1x1 transparent pixel
                # response = HttpResponse(content_type="image/png")
                # response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                # response['Pragma'] = 'no-cache'
                # response['Expires'] = '0'
                # response.write(png_data)
                
                response = FileResponse(png_data, content_type='image/png')
                response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'


                # Delete the token after use to prevent reuse
                # pixel_token.delete()

                return response
            else:
                # As file:
                # css_path = os.path.join(settings.BASE_DIR, 'static', 'empty.css')
                # with open(css_path, 'r') as css_file:
                #     css_data = css_file.read()

                # As hardcoded data
                css_data = ""

                # Serve an empty CSS file
                response = HttpResponse(content_type="text/css")
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                response.write(css_data)
                return response

    except TrackingPixelToken.DoesNotExist:
        return HttpResponse("Not found", status=404)

def serve_image(request, image_name):
    image_path = os.path.join(settings.BASE_DIR, 'static/images', image_name)
    if os.path.exists(image_path):
        with open(image_path, 'rb') as png_file:
            png_data = png_file.read()
            response = FileResponse(png_data, content_type="image/png")
            response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'


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

def track_email(request, email_id):
    try:
        email = Email.objects.get(id=email_id)
        TrackingLog.objects.create(
            email=email,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            opened_at=timezone.now()
        )
        # 1x1 transparent GIF data
        pixel = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff'
            b'\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x44\x01\x00\x3b'
        )
        return HttpResponse(pixel, content_type='image/gif')
    except Email.DoesNotExist:
        return HttpResponse(status=404)



def track_link(request, link_id):
    link = get_object_or_404(Link, pk=link_id)
    LinkClick.objects.create(
        link=link,
        clicked_at=datetime.now(),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
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