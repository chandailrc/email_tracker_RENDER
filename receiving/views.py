from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .receiving_utils import fetch_and_process_emails, process_incoming_email
from .models import ReceivedEmail

# @csrf_protect
# @require_http_methods(["POST"])
# The below function will be used lateron as an endpoint for receiving emails. 
# For example, we can configure the IMAP server (IONOS) to redirect any email as it receives to this end point
def receive_email(request):
    raw_email = request.body
    process_incoming_email(raw_email, request.user)
    return HttpResponse('Email received and processed', status=200)

@csrf_exempt
@require_POST
def fetch_emails(request):
    new_emails_count = fetch_and_process_emails(request.user)
    return JsonResponse({'new_emails': new_emails_count})

@require_GET
def list_emails(request):
    emails = ReceivedEmail.objects.filter(user=request.user).order_by('-received_at')
    email_list = [
        {
            'sender': email.sender,
            'subject': email.subject,
            'received_at': email.received_at.isoformat(),
        }
        for email in emails
    ]
    return JsonResponse({'emails': email_list})