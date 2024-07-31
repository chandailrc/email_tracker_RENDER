from django import forms
from .models import ContactList, Contact

class ContactListForm(forms.ModelForm):
    class Meta:
        model = ContactList
        fields = ['name']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'address', 'occupation', 'company']