from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import UserProfile

from django.contrib.auth import get_user_model
User = get_user_model() 

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    company = forms.CharField(max_length=100, required=False)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES, initial='free')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get('phone')
            user.profile.address = self.cleaned_data.get('address')
            user.profile.company = self.cleaned_data.get('company')
            user.profile.user_type = self.cleaned_data.get('user_type')
            user.profile.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    company = forms.CharField(max_length=100, required=False)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['phone'].initial = self.instance.profile.phone
            self.fields['address'].initial = self.instance.profile.address
            self.fields['company'].initial = self.instance.profile.company
            self.fields['user_type'].initial = self.instance.profile.user_type

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get('phone')
            user.profile.address = self.cleaned_data.get('address')
            user.profile.company = self.cleaned_data.get('company')
            user.profile.user_type = self.cleaned_data.get('user_type')
            user.profile.save()
        return user