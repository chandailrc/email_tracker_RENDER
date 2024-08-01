from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .forms import AdminUserCreationForm, AdminUserChangeForm

User = get_user_model()

@csrf_exempt
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return JsonResponse({
        'success': True,
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            } for user in page_obj
        ],
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })

@csrf_exempt
def user_detail(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'phone': user.phone,
                'address': user.address,
                'company': user.company,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        })
    elif request.method == 'POST':
        form = AdminUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'User updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    elif request.method == 'DELETE':
        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted successfully'})

@csrf_exempt
def user_create(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return JsonResponse({'success': True, 'message': 'User created successfully', 'user_id': user.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})