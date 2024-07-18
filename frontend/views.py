from django.shortcuts import render, redirect
from django.contrib import messages
from django.middleware.csrf import get_token

import requests

def compose_email_view(request):
    return render(request, 'compose_email.html')

def send_tracked_email_view(request):
    if request.method == 'POST':
        # Get the CSRF token
        csrf_token = get_token(request)
        
        # Include the CSRF token in the headers
        headers = {'X-CSRFToken': csrf_token}
        
        # Make sure to use the correct URL for your API
        response = requests.post('http://127.0.0.1:8000/api/sending/send-tracked-email/', 
                                 data=request.POST, 
                                 headers=headers, 
                                 cookies=request.COOKIES)  # Include cookies for CSRF
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                messages.success(request, result['message'])
                if result['failed_recipients']:
                    messages.warning(request, f"Failed to send to: {', '.join(result['failed_recipients'])}")
            else:
                messages.error(request, 'Failed to send email')
        else:
            messages.error(request, f'An error occurred: {response.status_code}')
        
        return redirect('compose_email')
    
    return render(request, 'compose_email.html')