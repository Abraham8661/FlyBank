from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import KYC, Account
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse
from users_auth.models import User
# Pagination
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def kyc_and_pin_checker(request):
    # Checking if user KYC is done
    all_kyc = KYC.objects.all()
    try:
        user_kyc = KYC.objects.get(user=request.user)
    except:
        user_kyc = None

    all_users_kyc_list = [kyc.user for kyc in all_kyc]
    user = request.user
    if user not in all_users_kyc_list:
        messages.error(
            request, "Sorry, you need to complete your KYC before using the feature!")
        return redirect("kyc")
    elif user in all_users_kyc_list and user_kyc.kyc_status != "approved":
        messages.error(
            request, "Sorry, your KYC needs to be approved before using the feature!")
        return redirect("dashboard")
    
    #Checking if PIN has been created
    account = Account.objects.get(user=request.user)
    if account.pin_number is None:
        messages.error(
            request, "Sorry, you need to create a four digit transaction before you continue!")
        return redirect("create-pin")


def kyc_checker(request):
    # Checking if user KYC is done
    all_kyc = KYC.objects.all()
    try:
        user_kyc = KYC.objects.get(user=request.user)
    except:
        user_kyc = None

    all_users_kyc_list = [kyc.user for kyc in all_kyc]
    user = request.user
    if user not in all_users_kyc_list:
        messages.error(
            request, "Sorry, you need to complete your KYC before using the feature!")
        return redirect("kyc")
    elif user in all_users_kyc_list and user_kyc.kyc_status != "approved":
        messages.error(
            request, "Sorry, your KYC needs to be approved before using the feature!")
        return redirect("dashboard")
    
    return user_kyc


def nav_greeting(request):
    try:
        current_user = KYC.objects.get(user=request.user).first_name
    except:
        current_user = request.user
    current_time = datetime.today()
    hour = current_time.hour
    morning = range(0, 12)
    afternoon = range(12, 17)
    evening = range(17, 24)
    global GREETING
    for num in morning:
        if num == hour:
            GREETING = "Good Morning"
    for num in afternoon:
        if num == hour:
            GREETING = "Good Afternoon"
    for num in evening:
        if num == hour:
            GREETING = "Good Evening"
    return GREETING, current_user


# Working With Paginator
def paginate_pages(request, TRANSACTION, results):
    page = request.GET.get("page")
    paginator = Paginator(TRANSACTION, results)
    try:
        TRANSACTION = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        TRANSACTION = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        TRANSACTION = paginator.page(page)

    left_index = (int(page) - 4)
    if left_index < 1:
        left_index = 1
    right_index = (int(page) + 5)
    if right_index > paginator.num_pages:
        right_index = paginator.num_pages + 1
    custom_range = range(left_index, right_index)

    return custom_range, TRANSACTION
