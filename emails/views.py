from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Email
from .services import fetch_emails as fetch_emails_service

def email_list(request):
    emails = Email.objects.all().order_by('-received_at')
    return render(request, 'email_list.html', {'emails': emails})

@csrf_exempt
def fetch_emails(request):
    if request.method == 'POST':
        try:
            fetch_emails_service()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_email(request, email_id):
    try:
        email = Email.objects.get(id=email_id)
        return JsonResponse({
            'id': email.id,
            'subject': email.subject,
            'sender': email.sender,
            'received_at': email.received_at.isoformat(),
            'body_html': email.body_html,
            'body_text': email.body_text,
        })
    except Email.DoesNotExist:
        return JsonResponse({'error': 'Email not found'}, status=404)

@csrf_exempt
def reply_to_email(request, email_id):
    if request.method == 'POST':
        # Implement email reply logic here
        # For now, we'll just return a success message
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})