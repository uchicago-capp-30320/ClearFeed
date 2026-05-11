from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import AppUser


class AppUserCreationForm(UserCreationForm):
    class Meta:
        model = AppUser
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"]

        if AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email
