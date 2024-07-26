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
        # Get the CSRF token
        csrf_token = get_token(request)
        
        # Include the CSRF token in the headers
        headers = {'X-CSRFToken': csrf_token}
        
        # Make sure to use the correct URL for your API
        response = requests.post(f'{settings.BASE_URL}/api/sending/send-tracked-email/', 
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

def dashboard(request):
    # Make a GET request to the backend API
    response = requests.get(f'{settings.BASE_URL}/api/tracking/dashboard-data/')
    
    if response.status_code == 200:
        data = response.json()
        # emails = json.loads(data['emails'])
        unsubscribed_emails = data['unsubscribed_emails']
        
        # Deserialize the email data
        email_objects = list(serializers.deserialize('json', data['emails']))
        
        # Extract the actual model instances
        emails = [obj.object for obj in email_objects]
        
        return render(request, 'dashboard.html', {
            'emails': emails, 
            'unsubscribed_emails': unsubscribed_emails
        })
    else:
        # Handle error case
        return render(request, 'dashboard.html', {
            'error': 'Failed to fetch dashboard data'
        })
    
def email_detail(request, email_id):
    
    response = requests.get(f'{settings.BASE_URL}/api/tracking/email-detail-data/?email_id={email_id}')
    
    if response.status_code == 200:
        data = response.json()
        # email = json.loads(data['email'])
        
        # Deserialize the email data
        email_object = list(serializers.deserialize('json', data['email']))[0]
        email = email_object.object
                        
        tracking_logs_objects = list(serializers.deserialize('json', data['tracking_logs']))
        tracking_logs = [obj.object for obj in tracking_logs_objects]
        
        link_clicks = serializers.deserialize('json', data['link_clicks'])
        link_clicks_objects = list(serializers.deserialize('json', data['link_clicks']))
        link_clicks = [obj.object for obj in link_clicks_objects]
        
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
            
            # Get the CSRF token
            csrf_token = get_token(request)
            
            # Include the CSRF token in the headers
            headers = {'X-CSRFToken': csrf_token}
            
            response = requests.post(
                f'{settings.BASE_URL}/api/unsubscribers/unsubscribe-action/',
                data={'user_email': user_email},
                headers=headers, 
                cookies=request.COOKIES 
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    if data['already_unsubscribed']:
                        message = "You were already unsubscribed."
                    else:
                        message = "You have been unsubscribed successfully."
                    return HttpResponse(message)
                else:
                    return HttpResponse(data['message'], status=400)
            else:
                return HttpResponse('Failed to process the unsubscribe request.', status=response.status_code)
    return render(request, 'unsubscribe.html', {'email': user_email})


def unsubscribed_users_list(request):
    
    response = requests.get(f'{settings.BASE_URL}/api/unsubscribers/unsubscribed-users-data/')
    
    if response.status_code == 200:
        data = response.json()
        unsubscribed_users = data['unsubscribed_emails']
        
        return render(request, 'unsubscribed_users_list.html', {'unsubscribed_emails': unsubscribed_users})
    else:
        return render(request, 'unsubscribed_users_list.html', {'error': 'Failed to fetch unsubscribe data'})

    
def delete_unsubscribed_user(request, user_email):
    
    if request.method == 'POST':
        
        # Get the CSRF token
        csrf_token = get_token(request)
        
        # Include the CSRF token in the headers
        headers = {'X-CSRFToken': csrf_token}
        
        response = requests.post(f'{settings.BASE_URL}/api/unsubscribers/delete-unsub-user/', 
                                 data={'user_email': user_email},
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
            return HttpResponse('Failed to process the deletion request.', status=response.status_code)

    return redirect('unsubscribed_users_list')

def email_management(request):
    # Make API call to get emails
    response = requests.get(f'{settings.BASE_URL}/api/receiving/list/')
    if response.status_code == 200:
        emails = response.json().get('emails', [])
    else:
        emails = []
        messages.error(request, "Failed to fetch emails from the server.")

    context = {
        'emails': emails,
    }
    return render(request, 'email_management.html', context)

def fetch_emails(request):
    if request.method == 'POST':
        
        # Get the CSRF token
        csrf_token = get_token(request)
        
        # Include the CSRF token in the headers
        headers = {'X-CSRFToken': csrf_token}
        # Make API call to fetch emails
        response = requests.post(f'{settings.BASE_URL}/api/receiving/fetch/',
                                 headers=headers,
                                 cookies=request.COOKIES 
                                 )
        if response.status_code == 200:
            new_emails_count = response.json().get('new_emails', 0)
            messages.success(request, f'Fetched {new_emails_count} new emails')
        else:
            messages.error(request, "Failed to fetch new emails.")
    return redirect('email_management')


def conversation_list(request):
    response = requests.get('http://localhost:8000/conversations/list/')
    conversations = response.json()['conversations']
    return render(request, 'frontend/conversation_list.html', {'conversations': conversations})

def conversation_detail(request, conversation_id):
    response = requests.get(f'http://localhost:8000/conversations/{conversation_id}/')
    conversation = response.json()
    return render(request, 'frontend/conversation_detail.html', {'conversation': conversation})