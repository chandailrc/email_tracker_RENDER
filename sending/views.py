import time
import random

from . import sending_utils

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from receiving.models import ReceivedEmail

@csrf_exempt
@require_POST
def send_tracked_email(request):
    recipients = request.POST.get('recipients', '').split()
    subject = request.POST.get('subject')
    body = request.POST.get('body')
    delay_type = request.POST.get('delay_type')
    delay_value = int(request.POST.get('delay_value', 0))
    min_delay = int(request.POST.get('min_delay', 0))
    max_delay = int(request.POST.get('max_delay', 0))

    sent_count = 0
    failed_recipients = []

    for recipient in recipients:
        recipient = recipient.strip()
        if recipient:
            success = sending_utils.tracked_email_sender(recipient, subject, body)
            if success:
                sent_count += 1
                print(f"views.py/send_tracked_email_view: Email sent successfully to {recipient}")
            else:
                failed_recipients.append(recipient)
                print(f"views.py/send_tracked_email_view: Failed to send email to {recipient}")
            
            if delay_type == 'fixed':
                time.sleep(delay_value)
            elif delay_type == 'random':
                time.sleep(random.uniform(min_delay, max_delay))

    confirmation_message = f"{sent_count} email(s) sent successfully!"
    print(confirmation_message)  # For debugging

    return JsonResponse({
        'success': True,
        'message': confirmation_message,
        'sent_count': sent_count,
        'failed_recipients': failed_recipients
    })

@csrf_protect
@require_POST
def reply_send_tracked_email(request, received_email_id):
    
    received_email = ReceivedEmail.objects.get(id=received_email_id)
    subject = request.POST.get('subject')
    body = request.POST.get('body')
    
    success = sending_utils.tracked_email_sender(received_email.sender, subject, body, in_reply_to=received_email)
    
    if success:
        confirmation_message = 'Reply sent successfully to {received_email.sender}'
        sent_count = 1
        failed_recipients = 0
    else:
        confirmation_message = 'Reply failed to {received_email.sender}'
        sent_count = 0
        failed_recipients = 1
    
    return JsonResponse({
        'success': True,
        'message': confirmation_message,
        'sent_count': sent_count,
        'failed_recipients': failed_recipients
    })

