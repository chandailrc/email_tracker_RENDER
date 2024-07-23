# receiving/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import ReceivedEmail
from .services.email_fetcher import fetch_emails_service
import json

def fetch_emails(request):
    if request.method == 'POST':
        result = fetch_emails_service()
        return JsonResponse({"message": result})
    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_received_emails(request):
    emails = ReceivedEmail.objects.all().order_by('-received_at')
    emails_data = [{
        'id': email.id,
        'sender': email.sender,
        'subject': email.subject,
        'received_at': email.received_at.isoformat(),
    } for email in emails]
    return JsonResponse(emails_data, safe=False)

def get_email_detail(request, email_id):
    email = get_object_or_404(ReceivedEmail, id=email_id)
    email_data = {
        'id': email.id,
        'sender': email.sender,
        'recipients': json.loads(email.recipients),
        'cc': json.loads(email.cc) if email.cc else None,
        'bcc': json.loads(email.bcc) if email.bcc else None,
        'subject': email.subject,
        'body': email.body,
        'html_body': email.html_body,
        'received_at': email.received_at.isoformat(),
        'attachments': [{
            'id': att.id,
            'filename': att.filename,
            'content_type': att.content_type,
            'size': att.size,
            'file_url': att.file.url,
        } for att in email.attachments.all()]
    }
    return JsonResponse(email_data)