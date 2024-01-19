from django.forms import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    class Meta:
        model= User
        fields = ("email",)

    def save(self, commit: bool = True) -> User:
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
    
        return User.objects.create_user(username=email, email=email, password=password)