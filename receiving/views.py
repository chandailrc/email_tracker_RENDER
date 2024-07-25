from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import fetch_and_process_emails, process_incoming_email
from .models import ReceivedEmail

@csrf_exempt
def receive_email(request):
    if request.method == 'POST':
        raw_email = request.body
        process_incoming_email(raw_email)
        return HttpResponse('Email received and processed', status=200)
    return HttpResponse('Invalid request', status=400)

def fetch_emails(request):
    if request.method == 'GET':
        new_emails_count = fetch_and_process_emails()
        return JsonResponse({'status': 'success', 'new_emails': new_emails_count})
    return HttpResponse('Invalid request', status=400)

def list_received_emails(request):
    emails = ReceivedEmail.objects.all().order_by('-received_at')
    email_list = [
        {
            'id': email.id,
            'sender': email.sender,
            'subject': email.subject,
            'received_at': email.received_at.isoformat()
        }
        for email in emails
    ]
    return JsonResponse({'emails': email_list})