from .models import UnsubscribedUser
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

@require_POST
@csrf_protect
def unsubscribe_action(request):
    user_email = request.POST.get('user_email')
    if user_email:
        unsubscribed, created = UnsubscribedUser.objects.get_or_create(email=user_email)
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
    unsubscribed_users = UnsubscribedUser.objects.values_list('email', flat=True)
    
    return JsonResponse({
        'unsubscribed_emails': list(unsubscribed_users)
    })


@require_POST
@csrf_protect
def delete_unsub_user(request):
    user_email = request.POST.get('user_email')
    if user_email:
        user = get_object_or_404(UnsubscribedUser, email=user_email)
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