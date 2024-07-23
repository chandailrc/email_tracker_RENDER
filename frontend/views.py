from django.shortcuts import render, redirect
from django.contrib import messages
from django.middleware.csrf import get_token
from django.conf import settings
from django.http import HttpResponse
from django.core import serializers

import requests

def compose_email_view(request):
    return render(request, 'compose_email.html')

def send_tracked_email_view(request):
    if request.method == 'POST':
        # Prepare the data
        data = {
            'recipients': request.POST.get('recipients', '').split(),
            'subject': request.POST.get('subject'),
            'body': request.POST.get('body'),
            'delay_type': request.POST.get('delay_type'),
            'delay_value': request.POST.get('delay_value'),
            'min_delay': request.POST.get('min_delay'),
            'max_delay': request.POST.get('max_delay'),
        }
        
        # Make sure to use the correct URL for your API
        response = requests.post(f'{settings.BASE_URL}/api/sending/send-tracked-email/', 
                                 json=data,
                                 headers={'Content-Type': 'application/json'},
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


def dashboard(request):
    response = requests.get(f'{settings.BASE_URL}/api/tracking/dashboard-data/')
    
    if response.status_code == 200:
        data = response.json()
        emails = data['emails']
        unsubscribed_emails = data['unsubscribed_emails']
        
        return render(request, 'dashboard.html', {
            'emails': emails, 
            'unsubscribed_emails': unsubscribed_emails
        })
    else:
        return render(request, 'dashboard.html', {
            'error': 'Failed to fetch dashboard data'
        })
    
def email_detail(request, email_id):
    response = requests.get(f'{settings.BASE_URL}/api/tracking/email-detail-data/?email_id={email_id}')
    
    if response.status_code == 200:
        data = response.json()
        
        # The data is now directly serialized, no need for deserialization
        email = data['email']
        tracking_logs = data['tracking_logs']
        link_clicks = data['link_clicks']
        
        context = {
            'email': email,
            'tracking_logs': tracking_logs,
            'link_clicks': link_clicks,
        }
        return render(request, 'email_detail.html', context)
    else:
        # Handle error case
        return render(request, 'email_detail.html', {
            'error': 'Failed to fetch email detail data'
        })

def unsubscribe(request):
    user_email = request.GET.get('email')
    if user_email:
        if request.method == 'POST':
            csrf_token = get_token(request)
            headers = {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json'  # Add this line
            }
            
            response = requests.post(
                f'{settings.BASE_URL}/api/unsubscribers/users/unsubscribe/',
                json={'user_email': user_email},  # Change data to json
                headers=headers, 
                cookies=request.COOKIES 
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    message = "You were already unsubscribed." if data['already_unsubscribed'] else "You have been unsubscribed successfully."
                    return HttpResponse(message)
                else:
                    return HttpResponse(data['message'], status=400)
            else:
                return HttpResponse(f'Failed to process the unsubscribe request. Status code: {response.status_code}', status=response.status_code)
    return render(request, 'unsubscribe.html', {'email': user_email})


def unsubscribed_users_list(request):
    response = requests.get(f'{settings.BASE_URL}/api/unsubscribers/users/unsubscribed_users/')  # Updated URL
    
    if response.status_code == 200:
        data = response.json()
        unsubscribed_users = data['unsubscribed_emails']
        return render(request, 'unsubscribed_users_list.html', {'unsubscribed_emails': unsubscribed_users})
    else:
        return render(request, 'unsubscribed_users_list.html', {'error': 'Failed to fetch unsubscribe data'})

    
def delete_unsubscribed_user(request, user_email):
    if request.method == 'POST':
        csrf_token = get_token(request)
        headers = {
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'  # Add this line
        }
        
        response = requests.post(
            f'{settings.BASE_URL}/api/unsubscribers/users/delete_unsub_user/',
            json={'user_email': user_email},  # Change data to json
            headers=headers,
            cookies=request.COOKIES 
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return redirect('unsubscribed_users_list')
            else:
                return HttpResponse(data['message'], status=400)
        else:
            return HttpResponse(f'Failed to process the deletion request. Status code: {response.status_code}', status=response.status_code)
    return redirect('unsubscribed_users_list')