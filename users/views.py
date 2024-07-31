from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return JsonResponse({'success': True, 'message': 'User registered successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'message': 'User logged in successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid credentials'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True, 'message': 'User logged out successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserChangeForm

@csrf_exempt
@login_required
def update_user(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'User updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_user_info(request):
    if request.user.is_authenticated:
        user = request.user
        return JsonResponse({
            'success': True,
            'user_info': {
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'phone': user.phone,
                'address': user.address,
                'company': user.company,
            }
        })
    return JsonResponse({'success': False, 'message': 'User not authenticated'})