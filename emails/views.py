from django.shortcuts import render
from .models import Email
from .services import fetch_emails
from django.contrib import messages
from django.core.paginator import Paginator

def email_list(request):
    if request.method == 'POST':
        try:
            fetch_emails()
            messages.success(request, "Emails fetched successfully.")
        except Exception as e:
            messages.error(request, f"Error fetching emails: {str(e)}")

    emails = Email.objects.all()
    paginator = Paginator(emails, 10)  # Show 10 emails per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'email_list.html', {'page_obj': page_obj})