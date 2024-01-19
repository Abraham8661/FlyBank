from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import KYC, Account, Transaction, ChargeManager, PaymentRequest, UserRecentManager
from django.contrib import messages
from account.extra import kyc_and_pin_checker, nav_greeting
from django.contrib.auth.hashers import make_password, check_password
from users_auth.models import User
from django.db.models import Q


def request_start_view(request):
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

    # Transfer Recents
    try:
        RECENT_TRANS = UserRecentManager.objects.get(user=request.user)
        ALL_TRANS = RECENT_TRANS.request_accounts.all().order_by("-date")[:5]
    except:
        RECENT_TRANS = None
        ALL_TRANS = None

    kyc_and_pin_checker(request)

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


    return render(request, "bank/receive1.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "account_searched": ACCOUNT_RETRIVED,
        "user_account": user_account,
        "recent": ALL_TRANS,
    })


def initiate_request(request, account_number):
    GREETING, current_user = nav_greeting(request)
    recipient_account = Account.objects.get(account_number=account_number)
    user_account = Account.objects.get(user=request.user)

    kyc_and_pin_checker(request)

    #The logic in charge of initiating a request
    if request.method == "POST":
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        payment_due = request.POST.get("payment-due")

        #Other details for the request method
        sender_account = Account.objects.get(user=request.user)

        #Creating a new request
        new_request = PaymentRequest.objects.create (
            sender = request.user,
            sender_account = sender_account,
            receiver_account = recipient_account,
            description = description,
            payment_due_by = payment_due,
            amount = amount,
            status = "processing",
        )

        new_request.save()

        return redirect("receive3", recipient_account.account_number, new_request.request_id)

    return render(request, "bank/receive2.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "recipient_account": recipient_account,
        "user_account": user_account,
    })


def process_request(request, account_number, request_id):
    GREETING, current_user = nav_greeting(request)
    receiver_account = Account.objects.get(account_number=account_number)
    sender_account = Account.objects.get(user=request.user)
    new_request = PaymentRequest.objects.get(request_id=request_id)

    kyc_and_pin_checker(request)

    # Process Request Logic
    if request.method == "POST":
        pin_code = request.POST.get("pin-code")
        document1 = request.FILES.get("document1")
        document2 = request.FILES.get("document2")
        document3 = request.FILES.get("document3")

        stored_pin_code = sender_account.pin_number
        check_pin = check_password(pin_code, stored_pin_code)
        if check_pin is True:
            #If pin is correct, attach the documents to the request model
            new_request.proof_doc1 = document1
            new_request.proof_doc2 = document2
            new_request.proof_doc3 = document3
            new_request.save()

            #send request and save request

            new_request.status = "request"
            new_request.save()

            # Add to recent manager
            trans_to_add_list = []
            if receiver_account not in trans_to_add_list:
                trans_to_add_list.append(receiver_account)

            try:
                trans_recent = UserRecentManager.objects.get(user=request.user)
                for account in trans_to_add_list:
                    trans_recent.request_accounts.add(account)
                trans_recent.save()
            except:
                trans_recent = UserRecentManager.objects.create(
                    user=request.user,
                    recent_type="paid_request",
                )
                trans_recent.request_accounts.set(trans_to_add_list)
                trans_recent.save()

            messages.success(request, f"Your request to {new_request.receiver_account.account_name} has been sent successfully")
            return redirect("request-success", receiver_account.account_number, new_request.request_id)
        
        else:
            messages.error(
                request, "Your pin code is incorrect, check your pin and try again")

    return render(request, "bank/receive3.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "recipient_account": receiver_account,
        "user_account": sender_account,
        "new_request": new_request
    })


def request_success(request, account_number, request_id):
    new_request = PaymentRequest.objects.get(request_id=request_id)
    return render(request, "bank/request_success.html", {
        "request": new_request
    })


def request_clearing_house(request):
    GREETING, current_user = nav_greeting(request)
    account = Account.objects.get(user=request.user)
    ALL_REQUESTS = None
    RECEIVED_REQUEST = None

    # This segment is for clearing and processing sent requests:
    if request.method == "POST":
        settle_request_id = request.POST.get("settle-request")

        try:
            #Logic to settle request
            request_involved = PaymentRequest.objects.get(request_id=settle_request_id)

            #Request details
            request_amount = request_involved.amount
            request_receiver_account = request_involved.sender_account
            description = request_involved.description
            receiver_account_number = request_receiver_account.account_number

            #Details for new transaction
            sender_account_balance = account.account_balance
            amount_to_float = float(request_amount)
            trans_fee = ChargeManager.objects.get(charge_id="FEE5346116290")
            receiver_instance = Account.objects.get(account_number=receiver_account_number)

            #Create new transaction
            if sender_account_balance > 0 and sender_account_balance > amount_to_float:
                new_transaction = Transaction.objects.create(
                    sender=request.user,
                    sender_account=account,
                    receiver_account=receiver_instance,
                    description=description,
                    amount=amount_to_float,
                    transaction_fee=trans_fee,
                    status="completed",
                    tranaction_type="paid_request",
                )
                new_transaction.save()

                #Substract the transaction amount from the sender and deduct the amount from the receiver
                trans_id = new_transaction.transaction_id
                transaction = Transaction.objects.get(transaction_id=trans_id)
                trans_amount = transaction.amount
                trans_fee = transaction.transaction_fee.fee
                sender_instance = Account.objects.get(user=request.user)
                sender_inst_acc_bal = sender_instance.account_balance
                sender_new_account_balance = sender_inst_acc_bal - trans_amount - trans_fee
                sender_inst_acc_bal = sender_new_account_balance
                sender_instance.account_balance = sender_new_account_balance
                sender_instance.save()


                #Add the transaction amount to the receiver and deduct the amount from the sender
                receiver_inst = Account.objects.get(account_number=receiver_account_number)
                receiver_account_balance = receiver_inst.account_balance
                receiver_new_account_balance = receiver_account_balance + trans_amount
                receiver_account_balance = receiver_new_account_balance
                receiver_inst.account_balance = receiver_new_account_balance
                receiver_inst.save()

                #Change the status of the request and save
                request_involved.status = "settled"
                request_involved.save()

                messages.success(request, f"You have settled your payment request from {request_receiver_account.account_name}")
                return redirect("request")

            else:
                messages.error(request, "Insufficient Funds")
        except:
            request_involved = None

        cancel_request_id = request.POST.get("cancel-request")
        #Logic to cancel request
        request_to_cancel = PaymentRequest.objects.get(request_id=cancel_request_id)
        request_to_cancel.status = "cancelled"
        request_to_cancel.save()
        messages.success(request, f"You have cancelled your payment request from {request_to_cancel.sender_account.account_name}")
        return redirect("request")   
    
    try:
        ALL_REQUESTS = PaymentRequest.objects.filter(
            Q(sender_account=account) | Q(receiver_account=account)
        )
        RECEIVED_REQUEST = PaymentRequest.objects.filter(receiver_account=account)
    except:
        ALL_REQUESTS = None
        RECEIVED_REQUEST = None
    
    return render(request, "bank/request.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "requests": ALL_REQUESTS,
        "account": account
    })
