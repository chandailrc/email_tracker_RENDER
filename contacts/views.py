from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import ContactList, Contact
from .forms import ContactListForm, ContactForm

@csrf_exempt
@login_required
def create_contact_list(request):
    if request.method == 'POST':
        form = ContactListForm(request.POST)
        if form.is_valid():
            contact_list = form.save(commit=False)
            contact_list.user = request.user
            contact_list.save()
            return JsonResponse({'success': True, 'id': contact_list.id, 'name': contact_list.name})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_contact_lists(request):
    contact_lists = ContactList.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({'success': True, 'contact_lists': list(contact_lists)})

@csrf_exempt
@login_required
def create_contact(request, list_id):
    try:
        contact_list = ContactList.objects.get(id=list_id, user=request.user)
    except ContactList.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Contact list not found'})

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.contact_list = contact_list
            contact.save()
            return JsonResponse({'success': True, 'id': contact.id, 'name': contact.name, 'email': contact.email})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_contacts(request, list_id):
    try:
        contact_list = ContactList.objects.get(id=list_id, user=request.user)
    except ContactList.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Contact list not found'})

    contacts = Contact.objects.filter(contact_list=contact_list).values('id', 'name', 'email', 'phone', 'address', 'occupation', 'company')
    return JsonResponse({'success': True, 'contacts': list(contacts)})

@csrf_exempt
@login_required
def update_contact(request, contact_id):
    try:
        contact = Contact.objects.get(id=contact_id, contact_list__user=request.user)
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Contact not found'})

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Contact updated successfully'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_contact(request, contact_id):
    try:
        contact = Contact.objects.get(id=contact_id, contact_list__user=request.user)
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Contact not found'})

    if request.method == 'POST':
        contact.delete()
        return JsonResponse({'success': True, 'message': 'Contact deleted successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})