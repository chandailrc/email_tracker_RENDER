from django.shortcuts import render
from .email_utils import fetch_emails

def inbox_view(request):
    emails = fetch_emails()
    return render(request, 'inbox.html', {'emails': emails})
