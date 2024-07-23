from django.shortcuts import render
from .models import Email
from .services import fetch_emails
from django.contrib import messages

def email_list(request):
    if request.method == 'POST':
        try:
            fetch_emails()
            messages.success(request, "Emails fetched successfully.")
        except Exception as e:
            messages.error(request, f"Error fetching emails: {str(e)}")
    emails = Email.objects.all().order_by('-received_at')
    return render(request, 'emails/email_list.html', {'emails': emails})