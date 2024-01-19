from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),

    #Login/Signup
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/signup/", views.signup_view, name="signup"),
    path("accounts/logout/", views.logout_view, name="logout"),
]
