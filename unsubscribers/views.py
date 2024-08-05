from .models import UnsubscribedUser
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth import get_user_model

@require_POST
@csrf_exempt
def unsubscribe_action(request):
    user_email = request.POST.get('user_email')
    sender_username = request.POST.get('sender_username')
    if user_email and sender_username:
        
        User = get_user_model()
        user = User.objects.get(username=sender_username)
        unsubscribed, created = UnsubscribedUser.objects.get_or_create(email=user_email,
                                                                       unsubscribed_from=user)
        return JsonResponse({
            'success': True,
            'message': 'You have been unsubscribed.',
            'already_unsubscribed': not created
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Email address is required.'
        }, status=400)

def unsubscribed_users_data(request):
    unsubscribed_users = UnsubscribedUser.objects.filter(unsubscribed_from=request.user).values_list('email', flat=True)    
    
    return JsonResponse({
        'unsubscribed_emails': list(unsubscribed_users)
    })


@require_POST
@csrf_exempt
def delete_unsub_user(request):
    user_email = request.POST.get('user_email')
    if user_email:
        user = get_object_or_404(UnsubscribedUser, email=user_email, unsubscribed_from=request.user)
        user.delete()
        return JsonResponse({
            'success': True,
            'message': f'User email {user_email} removed from unsubscribed list.'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Email address is required.'
        }, status=400)