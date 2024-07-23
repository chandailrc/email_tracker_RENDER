from django.shortcuts import render
from .models import Email
from .services import fetch_emails

def email_list(request):
    if request.method == 'POST':
        fetch_emails()
    emails = Email.objects.all().order_by('-received_at')
    return render(request, 'emails/email_list.html', {'emails': emails})