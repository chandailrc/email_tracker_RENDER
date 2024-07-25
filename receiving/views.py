from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .utils import fetch_and_process_emails, process_incoming_email
from .models import ReceivedEmail

@csrf_exempt
@require_http_methods(["POST"])
def receive_email(request):
    raw_email = request.body
    process_incoming_email(raw_email)
    return HttpResponse('Email received and processed', status=200)

@require_http_methods(["POST"])
def fetch_emails(request):
    new_emails_count = fetch_and_process_emails()
    return JsonResponse({'new_emails': new_emails_count})

@require_http_methods(["GET"])
def list_emails(request):
    emails = ReceivedEmail.objects.all().order_by('-received_at')
    email_list = [
        {
            'sender': email.sender,
            'subject': email.subject,
            'received_at': email.received_at.isoformat(),
        }
        for email in emails
    ]
    return JsonResponse({'emails': email_list})