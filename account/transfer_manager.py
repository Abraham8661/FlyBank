from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import KYC, Account, Transaction, ChargeManager, UserRecentManager, Notification
from django.contrib import messages
from account.extra import kyc_and_pin_checker, nav_greeting
from django.contrib.auth.hashers import make_password, check_password
from users_auth.models import User
from django.db.models import Q

#This manager is in charge of controlling transferring of money within the bank


@login_required
def transfer_start_view(request):
    GREETING, current_user = nav_greeting(request)
    ACCOUNT_RETRIVED = None
    RECENT_TRANS = None
    ALL_TRANS = None

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
    
    # Checking if PIN has been created
    account = Account.objects.get(user=request.user)
    if account.pin_number is None:
        messages.error(
            request, "Sorry, you need to create a four digit transaction before you continue!")
        return redirect("create-pin")
    

    user_account = Account.objects.get(user=request.user)

    #Transfer Recents
    try:
        RECENT_TRANS = UserRecentManager.objects.get(user=request.user)
        ALL_TRANS = RECENT_TRANS.transaction_accounts.all().order_by("-date")[:5]
    except:
        RECENT_TRANS = None
        ALL_TRANS = None

    try:
        # Search for Account
        if request.GET.get("account"):
            search_query = request.GET.get("account")

            ACCOUNT_RETRIVED = Account.objects.filter(Q(account_number__icontains=search_query) | Q(
                user__email__icontains=search_query) | Q(
                phone_number__icontains=search_query)).distinct()

            for account in ACCOUNT_RETRIVED:
                if account.account_number == user_account.account_number:
                    messages.error(
                        request, "You can't transfer money to your account")
                    return render("transfer1")
    except:
        ACCOUNT_RETRIVED = None
        RECENT_TRANS = None

    return render(request, "bank/transfer1.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "account_searched": ACCOUNT_RETRIVED,
        "user_account": user_account,
        "recent": ALL_TRANS,
 
    })


def initiate_transfer(request, account_number):
    GREETING, current_user = nav_greeting(request)
    receiver_account = Account.objects.get(account_number=account_number)
    user_account = Account.objects.get(user=request.user)
    trans_fee = ChargeManager.objects.get(charge_id="FEE1093773978")

    # This manager is incharge of checking for kyc and if in is created
    kyc_and_pin_checker(request)

    # Incharge of initiating a transaction
    if request.method == "POST":
        input_amount = request.POST.get("amount")
        description = request.POST.get("description")
        recipient_account_number = request.POST.get("recipient_account_number")

        # Comparing Amount to transfer with user account balance
        sender = request.user
        sender_account = Account.objects.get(user=request.user)
        sender_account_balance = sender_account.account_balance
        receiver_account = Account.objects.get(
            account_number=recipient_account_number)
        amount_to_float = float(input_amount)

        if sender_account_balance > 0 and sender_account_balance > amount_to_float:
            new_transaction = Transaction.objects.create(
                sender=sender,
                sender_account=sender_account,
                receiver_account=receiver_account,
                description=description,
                amount=float(input_amount),
                transaction_fee=trans_fee,
                status="pending",
                tranaction_type="cash_transfer",
            )
            new_transaction.save()
            return redirect("transfer3", recipient_account_number, new_transaction.transaction_id)
        else:
            messages.error(request, "Insufficient Funds")
            return redirect("transfer2", recipient_account_number)

    return render(request, "bank/transfer2.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "recipient_account": receiver_account,
        "user_account": user_account,
        "trans_fee": trans_fee,
    })


def process_transfer(request, account_number, trans_number):
    GREETING, current_user = nav_greeting(request)
    receiver_account = Account.objects.get(account_number=account_number)
    sender_account = Account.objects.get(user=request.user)
    transaction = Transaction.objects.get(transaction_id=trans_number)
    trans_fee = transaction.transaction_fee.fee
    kyc_and_pin_checker(request)

    # Process Transaction Logic
    if request.method == "POST":
        pin_code = request.POST.get("pin-code")
        stored_pin_code = sender_account.pin_number
        check_pin = check_password(pin_code, stored_pin_code)
        if check_pin is True:
            # Remove the amount from the sender account and add it to the receiver account
            amount = transaction.amount

            # Remove the amount from sender
            sender_account_balance = sender_account.account_balance
            new_sender_account_balance = sender_account_balance - amount - trans_fee
            sender_account.account_balance = new_sender_account_balance
            sender_account.save()

            # Add the amount to the receiver
            receiver_account_balance = receiver_account.account_balance
            new_receiver_account_balance = receiver_account_balance + amount 
            receiver_account.account_balance = new_receiver_account_balance
            receiver_account.save()

            # Change the status of transaction
            transaction.status = "completed"

            # Save Transaction, sender account and receiver account
            transaction.save()

            # Add to recent manager
            trans_to_add_list = []
            if receiver_account not in trans_to_add_list:
                trans_to_add_list.append(receiver_account)

            try:
                trans_recent = UserRecentManager.objects.get(user=request.user)
                for account in trans_to_add_list:
                    trans_recent.transaction_accounts.add(account)
                trans_recent.save()
            except:
                trans_recent = UserRecentManager.objects.create(
                    user = request.user,
                    recent_type="cash_transfer",
                )
                trans_recent.transaction_accounts.set(trans_to_add_list)
                trans_recent.save()

            messages.success(request, f"Your transfer to {
                             receiver_account.account_name} is successful")
            return redirect("transfer-success", receiver_account.account_number, transaction.transaction_id)
        else:
            messages.error(
                request, "Your pin code is incorrect, check your pin and try again")

    return render(request, "bank/transfer3.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "recipient_account": receiver_account,
        "user_account": sender_account,
        "transaction": transaction
    })


def transfer_success(request, account_number, trans_number):
    transaction = Transaction.objects.get(transaction_id=trans_number)
    return render(request, "bank/transfer_success.html", {
        "transaction": transaction
    })
       