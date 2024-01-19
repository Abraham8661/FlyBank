from django.shortcuts import render, redirect
from users_auth.forms import SignUpForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from users_auth.models import User


def home_view(request):
    user = request.user
    if user.is_authenticated:
        messages.success(
                request, "You are already logged in!")
        return redirect("dashboard")
    return render(request, "bankhall/index.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        all_users = User.objects.all()
        all_users_email = [user.email for user in all_users]
        try:
            user = authenticate(request, email=email, password=password)
            login(request, user)
            messages.success(
                request, "Login successful, Welcome Back!")
            return redirect("dashboard")
        except:
            if email not in all_users_email:
                messages.error(request, "This email does not exist, create an account instead!")
            else:
                messages.error(request, "Your password is incorrect!")
    return render(request, "bankhall/login.html")


def signup_view(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]
            try:
                user = authenticate(request, email=email, password=password)
                login(request, user)
            except:
                messages.error(request, "There was an error, try again!")

            messages.success(
                request, "Account created successfully🎉 Welcome to FlyBank!")
            return redirect("dashboard")
    return render(request, "bankhall/signup.html", {
        "sign_up_form": form
    })


def logout_view(request):
    user = request.user
    if user.is_authenticated:
        logout(request)
        messages.success(
                request, "You are logged out, See you soon!")
        return redirect("home")