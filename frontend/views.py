from django.shortcuts import render, redirect
from django.contrib import messages
from django.middleware.csrf import get_token
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import requests

def home(request):
    return render(request, 'home.html')

@login_required
def compose_email_view(request):
    return render(request, 'compose_email.html')

@login_required
def send_tracked_email_view(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        
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

@login_required
def reply_send_tracked_email_view(request):
    conversation_id = request.POST.get('conversation_id')
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {
        'X-CSRFToken': csrf_token,
        'Cookie': f'sessionid={session_cookie}'
    }
    
    response = requests.post(
        f'{settings.BASE_URL}/api/sending/reply-send-tracked-email/',
        data=request.POST,
        headers=headers,
        cookies=request.COOKIES
    )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            message = 'Reply sent successfully.'
            status = 'success'
        else:
            message = f'Failed to send reply: {result.get("message", "Unknown error")}'
            status = 'error'
    else:
        message = f'An error occurred: {response.status_code}'
        status = 'error'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': status,
            'message': message,
            'conversation_id': conversation_id
        })
    else:
        if status == 'success':
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('conversation_detail', conversation_id=conversation_id)


from django.core.paginator import Paginator
from django.db.models import Count

@login_required
def dashboard(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/tracking/dashboard-data/', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        unsubscribed_emails = data['unsubscribed_users']
        
        # Deserialize the email data
        email_objects = list(serializers.deserialize('json', data['emails']))
        
        # Extract the actual model instances and reverse the order
        emails = [obj.object for obj in email_objects][::-1]
        
        # Paginate emails
        paginator = Paginator(emails, 9)  # Show 9 emails per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Prepare data for charts (only for current page)
        email_subjects = [email.subject[:20] + '...' if len(email.subject) > 20 else email.subject for email in page_obj][::-1]
        email_opens = [email.trackingitem_set.count() for email in page_obj][::-1]
        
        subscribed_count = len(emails) - len(unsubscribed_emails)
        unsubscribed_count = len(unsubscribed_emails)
        
        context = {
            'page_obj': page_obj, 
            'unsubscribed_emails': unsubscribed_emails,
            'email_subjects': email_subjects,
            'email_opens': email_opens,
            'subscribed_count': subscribed_count,
            'unsubscribed_count': unsubscribed_count,
        }
        
        return render(request, 'dashboard.html', context)
    else:
        # Handle error case
        return render(request, 'dashboard.html', {
            'error': 'Failed to fetch dashboard data'
        })

@login_required
def email_detail(request, email_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/tracking/email-detail-data/?email_id={email_id}', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Deserialize the email data
        email_object = list(serializers.deserialize('json', data['email']))[0]
        email = email_object.object
                        
        pixel_events_objects = list(serializers.deserialize('json', data['pixel_events']))
        pixel_events = [obj.object for obj in pixel_events_objects]
        
        link_events_objects = list(serializers.deserialize('json', data['link_events']))
        link_events = [obj.object for obj in link_events_objects]
        
        context = {
            'email': email,
            'pixel_events': pixel_events,
            'link_events': link_events,
        }
        return render(request, 'email_detail.html', context)
    else:
        # Handle error case
        return render(request, 'email_detail.html', {
            'error': 'Failed to fetch email detail data'
        })


def unsubscribe(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    user_email = request.GET.get('email')
    encoded_senderUser = request.GET.get('sender')
    if user_email and encoded_senderUser:
        if request.method == 'POST':
                       
                      
            response = requests.post(
                f'{settings.BASE_URL}/api/unsubscribers/unsubscribe-action/',
                data={'user_email': user_email,
                      'encoded_senderUser': encoded_senderUser},
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

@login_required
def unsubscribed_users_list(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/unsubscribers/unsubscribed-users-data/', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        unsubscribed_users = data['unsubscribed_emails']
        
        return render(request, 'unsubscribed_users_list.html', {'unsubscribed_emails': unsubscribed_users})
    else:
        return render(request, 'unsubscribed_users_list.html', {'error': 'Failed to fetch unsubscribe data'})

@login_required   
def delete_unsubscribed_user(request, user_email):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        
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

@login_required
def email_management(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/receiving/list/', headers=headers)
    if response.status_code == 200:
        emails = response.json().get('emails', [])
    else:
        emails = []
        messages.error(request, "Failed to fetch emails from the server.")

    context = {
        'emails': emails,
    }
    return render(request, 'email_management.html', context)

@csrf_exempt
@login_required
def fetch_emails(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/receiving/fetch/',
                                 headers=headers,
                                 cookies=request.COOKIES)
        if response.status_code == 200:
            new_emails_count = response.json().get('new_emails', 0)
            return JsonResponse({'status': 'success', 'new_emails_count': new_emails_count})
        else:
            return JsonResponse({'status': 'error', 'message': "Failed to fetch new emails."})
    return JsonResponse({'status': 'error', 'message': "Invalid request method."})

# @login_required
# def conversation_list(request):
#     csrf_token = get_token(request)
#     session_cookie = request.COOKIES.get('sessionid')
#     headers = {'X-CSRFToken': csrf_token,
#                'Cookie': f'sessionid={session_cookie}'}
    
#     response = requests.get(f'{settings.BASE_URL}/api/conversations/list/', headers=headers)
#     conversations = response.json()['conversations']
#     return render(request, 'conversation_list.html', {'conversations': conversations})

@login_required
def conversation_list(request, conversation_id=None):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/conversations/list/', headers=headers)
    conversations = response.json()['conversations']

    active_conversation = None
    recipient_email = ''
    last_email_id = None
    sendOrRec_status = None
    conversation_selected = False  # Initialize to False

    if conversations:
        if conversation_id:
            active_conversation_id = conversation_id
        else:
            active_conversation_id = None #request.GET.get('active', conversations[0]['id'])
        
        if active_conversation_id:
            conversation_response = requests.get(f'{settings.BASE_URL}/api/conversations/{active_conversation_id}/', headers=headers)
            active_conversation = conversation_response.json()            

        if active_conversation:
            conversation_selected = True  # Set to True when there's an active conversation

            # Determine the recipient's email (the other participant)
            user_email = settings.DEFAULT_FROM_EMAIL
            recipient_email = next((email for email in active_conversation['participants'] if email != user_email), '')
            
            last_email = active_conversation['messages'][-1] if active_conversation['messages'] else None
            last_email_id = last_email['email_id'] if last_email else None
            sendOrRec_status = last_email['sendOrRec'] if last_email else None

    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'conversation_selected': conversation_selected,
        'recipient_email': recipient_email,
        'last_email_id': last_email_id,
        'sendOrRec': sendOrRec_status
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # This is an AJAX request
        return JsonResponse({
            'conversation': active_conversation,
            'recipient_email': recipient_email,
            'last_email_id': last_email_id,
            'sendOrRec': sendOrRec_status
        })
    
    # Regular request, return the full page
    return render(request, 'whatsapp_style_conversations.html', context)

@login_required
def get_latest_conversations(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/conversations/list/', headers=headers)
    if response.status_code == 200:
        conversations = response.json()['conversations']
        return JsonResponse({'conversations': conversations})
    else:
        return JsonResponse({'error': 'Failed to fetch conversations'}, status=400)

@login_required
def mark_conversation_read(request, conversation_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/conversations/update_unread/{conversation_id}/', headers=headers)
    
    # Debugging: print the response text
    # print(f'Response status code: {response.status_code}')
    # print(f'Response content: {response.text}')
    
    if response.status_code == 200:
        response_success = response.json()
        print(f'mcr: Conversation marking as read: {response_success} for conversation id: {conversation_id}')
        return JsonResponse({'status': response_success['status'],
                             'last_updated': response_success['last_updated']})
    else:
        return JsonResponse({'error': f'Failed to update conversation {conversation_id}\'s unread status'}, status=400)

@login_required
def sync_unread_conversations(request):
        
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/conversations/fetch_unread_id_list/', headers=headers)
    
    # Debugging: print the response text
    # print(f'Request headers: {request.headers}')
    # print(f'Response status code: {response.status_code}')
    # print(f'Response content: {response.text}')
    
    if response.status_code == 200:
        unread_ids_wConversations = response.json()
        
        return JsonResponse({
            'unread_conversations': unread_ids_wConversations['unread_conversations'],
            'conversations': unread_ids_wConversations['conversations']
        })
    else:
        return JsonResponse({'error': 'Failed to sync/fetch unread ids and covnersations'}, status=400)

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

def handle_register(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/users/register/', data=request.POST, headers=headers)
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


from django.contrib.auth import authenticate

def handle_login(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
            
        response = requests.post(f'{settings.BASE_URL}/api/users/login/', 
                                 data=request.POST,
                                 headers=headers,
                                 cookies=request.COOKIES 
                                 )
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

from django.contrib.auth import logout as auth_logout

@login_required
def handle_logout(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/users/logout/', headers=headers)
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

from django.contrib.auth.decorators import login_required

@login_required
def handle_update_profile(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        # Include the session cookie in the request
        cookies = {'sessionid': request.COOKIES.get('sessionid')}
        response = requests.post(f'{settings.BASE_URL}/api/users/update/', data=request.POST, cookies=cookies, headers=headers)
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

from django.contrib.auth.decorators import login_required

@login_required
def contact_lists_page(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/contacts/lists/', cookies={'sessionid': request.COOKIES.get('sessionid')}, headers=headers)
    if response.status_code == 200:
        contact_lists = response.json().get('contact_lists', [])
        return render(request, 'contacts/contact_lists.html', {'contact_lists': contact_lists})
    else:
        return render(request, 'contacts/contact_lists.html', {'error': 'Failed to fetch contact lists'})

@login_required
def create_contact_list_page(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/lists/create/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')},
                                 headers=headers)
        if response.status_code == 200:
            return redirect('contact_lists_page')
        else:
            error = response.json().get('errors', 'Failed to create contact list')
            return render(request, 'contacts/create_contact_list.html', {'error': error})
    return render(request, 'contacts/create_contact_list.html')

@login_required
def contacts_in_list_page(request, list_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/contacts/lists/{list_id}/contacts/', 
                            cookies={'sessionid': request.COOKIES.get('sessionid')},
                            headers=headers)
    if response.status_code == 200:
        contacts = response.json().get('contacts', [])
        return render(request, 'contacts/contacts_in_list.html', {'contacts': contacts, 'list_id': list_id})
    else:
        return render(request, 'contacts/contacts_in_list.html', {'error': 'Failed to fetch contacts'})

@login_required
def create_contact_page(request, list_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/lists/{list_id}/contacts/create/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')},
                                 headers=headers)
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=list_id)
        else:
            error = response.json().get('errors', 'Failed to create contact')
            return render(request, 'contacts/create_contact.html', {'error': error, 'list_id': list_id})
    return render(request, 'contacts/create_contact.html', {'list_id': list_id})

@login_required
def update_contact_page(request, contact_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/update/', 
                                 data=request.POST, 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')},
                                 headers=headers)
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))
        else:
            error = response.json().get('errors', 'Failed to update contact')
            return render(request, 'contacts/update_contact.html', {'error': error, 'contact_id': contact_id})
    
    # Fetch current contact data
    response = requests.get(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/', 
                            cookies={'sessionid': request.COOKIES.get('sessionid')},
                            headers=headers)
    if response.status_code == 200:
        contact = response.json().get('contact', {})
        return render(request, 'contacts/update_contact.html', {'contact': contact})
    else:
        return render(request, 'contacts/update_contact.html', {'error': 'Failed to fetch contact data'})

@login_required
def delete_contact(request, contact_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/contacts/contacts/{contact_id}/delete/', 
                                 cookies={'sessionid': request.COOKIES.get('sessionid')},
                                 headers=headers)
        if response.status_code == 200:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))
        else:
            return redirect('contacts_in_list_page', list_id=request.POST.get('list_id'))
        
        
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_user_list(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    response = requests.get(f'{settings.BASE_URL}/api/adminUserManagement/users/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        return render(request, 'adminUserManagement/admin_user_list.html', {'users': data['users'], 'pagination': data})
    messages.error(request, 'Failed to fetch user list')
    return redirect('home')

@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/adminUserManagement/users/{user_id}/', data=request.POST, headers=headers)
    elif request.method == 'DELETE':
        response = requests.delete(f'{settings.BASE_URL}/api/adminUserManagement/users/{user_id}/', headers=headers)
    else:
        response = requests.get(f'{settings.BASE_URL}/api/adminUserManagement/users/{user_id}/', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if request.method == 'DELETE':
            messages.success(request, 'User deleted successfully')
            return redirect('admin_user_list')
        return render(request, 'adminUserManagement/admin_user_detail.html', {'user': data['user']})
    messages.error(request, 'Failed to fetch or update user information')
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def admin_user_create(request):
    csrf_token = get_token(request)
    session_cookie = request.COOKIES.get('sessionid')
    headers = {'X-CSRFToken': csrf_token,
               'Cookie': f'sessionid={session_cookie}'}
    
    if request.method == 'POST':
        response = requests.post(f'{settings.BASE_URL}/api/adminUserManagement/users/create/', data=request.POST, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                messages.success(request, 'User created successfully')
                return redirect('admin_user_detail', user_id=data['user_id'])
            else:
                messages.error(request, 'Failed to create user')
        else:
            messages.error(request, 'Failed to create user')
    return render(request, 'adminUserManagement/admin_user_create.html')