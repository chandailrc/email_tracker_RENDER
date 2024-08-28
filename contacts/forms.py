from django import forms
from .models import ContactList, Contact

class ContactListForm(forms.ModelForm):
    class Meta:
        model = ContactList
        fields = ['name']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'address', 'occupation', 'company',
                  'company_size', 'industry', 'location', 'technology_stack',
                  'budget', 'decision_maker_role', 'pain_points', 'previous_engagement']