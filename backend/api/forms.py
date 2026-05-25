from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import AppUser
from django.core.mail import send_mail
from django.conf import settings


class AppUserCreationForm(UserCreationForm):
    class Meta:
        model = AppUser
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"]

        if AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email
    
class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your Name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Your Email',
            'class': 'form-control'
        })
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'placeholder': 'Your Message',
            'class': 'form-control',
            'rows': 5
        })
    )
