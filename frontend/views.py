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
        csrf_token = get_token(request)
        headers = {'X-CSRFToken': csrf_token}
        
        response = requests.post(f'{settings.BASE_URL}/api/sending/send-tracked-email/', 
                                 data=request.POST, 
                                 headers=headers, 
                                 cookies=request.COOKIES)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                messages.success(request, result['message'])
                if result['failed_recipients']:
                    for recipient, error in result['errors'].items():
                        messages.warning(request, f"Failed to send to {recipient}: {error}")
            else:
                messages.error(request, 'Failed to send all emails')
                for recipient, error in result['errors'].items():
                    messages.warning(request, f"Failed to send to {recipient}: {error}")
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
    response = requests.get(f'{settings.BASE_URL}/api/conversations/list/')
    conversations = response.json()['conversations']
    return render(request, 'conversation_list.html', {'conversations': conversations})

def conversation_detail(request, conversation_id):
    response = requests.get(f'{settings.BASE_URL}/api/conversations/{conversation_id}/')
    conversation = response.json()
    return render(request, 'conversation_detail.html', {'conversation': conversation})

from django.contrib.auth.decorators import login_required

def register_page(request):
    return render(request, 'users/register.html')

def login_page(request):
    return render(request, 'users/login.html')

@login_required
def profile_page(request):
    return render(request, 'users/profile.html')

@login_required
def update_profile_page(request):
    return render(request, 'users/update_profile.html')

from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model

def handle_register(request):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/users/register/', data=request.POST)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Headers: {response.headers}")
        
        try:
            json_response = response.json()
            if json_response['success']:
                # Log the user in
                # ... (login logic here)
                return redirect('profile_page')
            else:
                return render(request, 'users/register.html', {'errors': json_response.get('errors', 'Registration failed')})
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            return render(request, 'users/register.html', {'errors': 'An error occurred during registration'})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'users/register.html', {'errors': 'An unexpected error occurred'})
    
    return render(request, 'users/register.html')

import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate

def handle_login(request):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/users/login/', data=request.POST)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Headers: {response.headers}")
        
        try:
            json_response = response.json()
            if json_response['success']:
                # Log the user in
                # You might need to adjust this part depending on how you're handling authentication
                user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
                if user is not None:
                    auth_login(request, user)
                    return redirect('profile_page')
            return render(request, 'users/login.html', {'error': json_response.get('message', 'Login failed')})
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            return render(request, 'users/login.html', {'error': 'An error occurred during login'})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'users/login.html', {'error': 'An unexpected error occurred'})
    
    return render(request, 'users/login.html')

import requests
from django.shortcuts import redirect
from django.conf import settings

import requests
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import logout as auth_logout

@login_required
def handle_logout(request):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/users/logout/')
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Headers: {response.headers}")
        
        try:
            json_response = response.json()
            if json_response['success']:
                # Clear any session data on the frontend
                auth_logout(request)
            return redirect('login_page')
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            # Even if there's an error, we should still log the user out
            auth_logout(request)
            return redirect('login_page')
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            # Even if there's an error, we should still log the user out
            auth_logout(request)
            return redirect('login_page')
    
    return redirect('profile_page')

import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def handle_update_profile(request):
    if request.method == 'POST':
        # Include the session cookie in the request
        cookies = {'sessionid': request.COOKIES.get('sessionid')}
        response = requests.post(f'{settings.BASE_URL}/api/users/update/', data=request.POST, cookies=cookies)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Headers: {response.headers}")
        
        try:
            json_response = response.json()
            if json_response['success']:
                return redirect('profile_page')
            else:
                return render(request, 'users/update_profile.html', {'errors': json_response.get('errors', 'Update failed')})
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSONDecodeError: {str(e)}")
            return render(request, 'users/update_profile.html', {'errors': 'An error occurred during profile update'})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'users/update_profile.html', {'errors': 'An unexpected error occurred'})
    
    return redirect('update_profile_page')


import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

@login_required
def contact_lists_page(request):
    response = requests.get(f'{settings.BASE_URL}/api/contacts/lists/', cookies={'sessionid': request.COOKIES.get('sessionid')})
    if response.status_code == 200:
        contact_lists = response.json().get('contact_lists', [])
        return render(request, 'contacts/contact_lists.html', {'contact_lists': contact_lists})
    else:
        return render(request, 'contacts/contact_lists.html', {'error': 'Failed to fetch contact lists'})

@login_required
def create_contact_list_page(request):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/lists/create/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')})
        if response.status_code == 200:
            return redirect('contact_lists_page')
        else:
            error = response.json().get('errors', 'Failed to create contact list')
            return render(request, 'contacts/create_contact_list.html', {'error': error})
    return render(request, 'contacts/create_contact_list.html')

@login_required
def contacts_in_list_page(request, list_id):
    response = requests.get(f'{settings.BASE_URL}/api/contacts/lists/{list_id}/contacts/', 
                            cookies={'sessionid': request.COOKIES.get('sessionid')})
    if response.status_code == 200:
        contacts = response.json().get('contacts', [])
        return render(request, 'contacts/contacts_in_list.html', {'contacts': contacts, 'list_id': list_id})
    else:
        return render(request, 'contacts/contacts_in_list.html', {'error': 'Failed to fetch contacts'})

@login_required
def create_contact_page(request, list_id):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/lists/{list_id}/contacts/create/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')})
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=list_id)
        else:
            error = response.json().get('errors', 'Failed to create contact')
            return render(request, 'contacts/create_contact.html', {'error': error, 'list_id': list_id})
    return render(request, 'contacts/create_contact.html', {'list_id': list_id})

@login_required
def update_contact_page(request, contact_id):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/update/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')})
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))
        else:
            error = response.json().get('errors', 'Failed to update contact')
            return render(request, 'contacts/update_contact.html', {'error': error, 'contact_id': contact_id})
    
    # Fetch current contact data
    response = requests.get(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/', 
                            cookies={'sessionid': request.COOKIES.get('sessionid')})
    if response.status_code == 200:
        contact = response.json().get('contact', {})
        return render(request, 'contacts/update_contact.html', {'contact': contact})
    else:
        return render(request, 'contacts/update_contact.html', {'error': 'Failed to fetch contact data'})

@login_required
def delete_contact(request, contact_id):
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/delete/', 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')})
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))
        else:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))