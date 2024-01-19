from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import KYC, Account, Transaction, ChargeManager, PaymentRequest, Notification, CreditCard
from django.contrib import messages
from account.extra import kyc_and_pin_checker, nav_greeting, paginate_pages
from django.contrib.auth.hashers import make_password, check_password
from users_auth.models import User
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash

from django.http import FileResponse
from django.views import View
from datetime import date

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa



#KYC VIEW
@login_required
def kyc_view(request):
    GREETING, current_user = nav_greeting(request)
    user = request.user
    account = Account.objects.get(user=user)
    try:
        #Checking If KYC Done
        user_kyc = KYC.objects.get(user=request.user)
        if user_kyc:
            messages.error(
                request, "You have done KYC already!")
            return redirect("dashboard")
    except:

        #Creating KYC
        if request.method == "POST":
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            email_address = request.POST.get("email_address")
            phone_number = request.POST.get("phone_number")
            country = request.POST.get("country")
            state = request.POST.get("state")
            address = request.POST.get("address")
            date_of_birth = request.POST.get("date_of_birth")
            gender = request.POST.get("gender")
            identity_doc = request.POST.get("identity_doc")
            front_card = request.FILES.get("front_card")
            back_card = request.FILES.get("back_card")
            signature = request.FILES.get("signature")
            passport = request.FILES.get("passport")
            
            KYC.objects.create(
                user = current_user,
                account = account,
                first_name = first_name,
                last_name = last_name,
                phone_number = phone_number,
                country = country,
                state = state,
                address = address,
                date_of_birth = date_of_birth,
                gender = gender,
                identity_document = identity_doc,
                identity_image_front = front_card,
                identity_image_back = back_card,
                signature = signature,
                passport = passport,
                kyc_status="in_review",
            )

            #Updating Account Model With Account Name and Phone number
            account.phone_number = phone_number
            account.account_name = first_name + " " + last_name
            account.account_image = passport
            account.account_status = "active"
            account.save()

            messages.success(
                request, "Awesome, your KYC has been submitted for review. It will be reviewed shortly!")
            return redirect("dashboard")
    
    
    return render(request, "bank/kyc.html", {
        "user": user,
        "account": account,
        "greeting": GREETING,
        "current_user": current_user,
    })


@login_required
def dashboard_view(request):
    account = Account.objects.get(user=request.user)
    total_payouts = 0 
    last_received = None
    all_cards = []
    stored_pin = ""
    #Transaction Section
    TRANSACTION = None
    try:
        TRANSACTION = Transaction.objects.filter(
                Q(sender_account=account) | Q(receiver_account=account)
        ).order_by("-date")[:5]
    except:
        TRANSACTION = None
    #End of transaction section
        
    #Request Section
    REQUESTS = []
    try:
        REQUESTS = PaymentRequest.objects.filter(receiver_account=account, status="request").exclude(sender_account=account).order_by(
            "-date")[:5]
    except:
        REQUESTS = []
    #End of request section
          
    try:
        # payouts
        payouts = Transaction.objects.filter(sender_account=account)
        all_payouts = [trans.amount for trans in payouts]
        total_payouts = sum(all_payouts)
        all_cards = CreditCard.objects.filter(user=request.user)

        #last received 
        last_received = Transaction.objects.filter(receiver_account=account).order_by("-date").first()
    except:
        total_payouts = 0
        last_received = None
        all_cards = []

    #Add Card Logic
    if request.method == "POST":
        if "chosen-card" and "pin-code" in request.POST:
            chosen_card = request.POST.get("chosen-card")
            pin_code = request.POST.get("pin-code")

            # Checking if user KYC is done
            all_kyc = KYC.objects.all()
            try:
                user_kyc = KYC.objects.get(user=request.user)
                stored_pin = account.pin_number
            except:
                user_kyc = None
                stored_pin = None

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
            else:
                check_pin = check_password(pin_code, stored_pin)
                current_date = date.today()
                expiry_date = date(current_date.year + 3, current_date.month, current_date.day)
                if check_pin:
                    new_credit_card = CreditCard.objects.create(
                        user = request.user,
                        account = account,
                        card_type = chosen_card,
                        card_name = account.account_name,
                        issue_date = current_date,
                        expiry_date = expiry_date
                    )
                    new_credit_card.save()

                    #Substracting the card fee from the user account
                    user_account_balance = account.account_balance
                    new_balance = user_account_balance - 1000
                    account.account_balance = new_balance
                    account.save()

                    #Creating a new transaction
                    new_transaction = Transaction.objects.create(
                        sender = request.user,
                        sender_account = account,
                        receiver_account = account,
                        description = f"Purchase of {new_credit_card.card_type} credit card",
                        amount = 1000,
                        status = "completed",
                        tranaction_type="card_purchase",
                    )
                    new_transaction.save()

                    messages.success(request, "You have successfully created a new credit card!")
                    return redirect("dashboard")

        #Fund Card Logic       
        elif "card-id" and "amount-to-fund" and "fund-card-pin-code" in request.POST:
            card_id = request.POST.get("card-id")
            amount_to_fund = request.POST.get("amount-to-fund")
            fund_card_pin_code = request.POST.get("fund-card-pin-code")
            try:
                stored_pin = account.pin_number
                credit_card_instance = CreditCard.objects.get(card_code=card_id)
            except:
                stored_pin = account.pin_number
                credit_card_instance = None
            
            check_user_pin = check_password(fund_card_pin_code, stored_pin)
            if check_user_pin:
                new_card_balance = credit_card_instance.card_balance + float(amount_to_fund)
                credit_card_instance.card_balance = new_card_balance
                credit_card_instance.save()

                #Deduct amount added to credit card from your user account balance
                new_user_acc_bal = account.account_balance - float(amount_to_fund)
                account.account_balance = new_user_acc_bal
                account.save()
            
                #Creating of new transaction
                new_transaction = Transaction.objects.create(
                        sender = request.user,
                        sender_account = account,
                    receiver_account=account,
                        description = f"Funding of {credit_card_instance.card_type} credit card",
                        amount = amount_to_fund,
                        status = "completed",
                        tranaction_type = "card_funding",
                    )
                new_transaction.save()

                messages.success(request, f"You have successfully funded your credit card with N{amount_to_fund}")
                return redirect("dashboard")
            else:
                messages.error(
                    request, "Your pin code is incorrect, check your pin and try again")
                
        elif "delete-card-id" and "delete-card-pin-code" in request.POST:
            delete_card_id = request.POST.get("delete-card-id")
            delete_pin_code = request.POST.get("delete-card-pin-code")
            try:
                the_credit_card = CreditCard.objects.get(card_code=delete_card_id)
                stored_pin = account.pin_number
            except:
                the_credit_card = None
                stored_pin = ""

            check_user_pin = check_password(delete_pin_code, stored_pin)
            if check_user_pin:

                #Add the card balance to user account balance
                credit_card_balance = the_credit_card.card_balance
                current_account_balance = account.account_balance
                new_acc_bal = current_account_balance + credit_card_balance
                account.account_balance = new_acc_bal
                account.save()

                #Delete card
                the_credit_card.delete()

                #Creating of new transaction
                new_transaction = Transaction.objects.create(
                        sender = request.user,
                        sender_account = account,
                    receiver_account=account,
                        description = f"Deleted credit card balance added to account balance",
                        amount = credit_card_balance,
                        status = "completed",
                        tranaction_type = "card_withdrawal",
                    )
                new_transaction.save()

                messages.success(request, "You have successfully deleted your credit card")
                return redirect("dashboard")
            
            else:
                messages.error(
                    request, "Your pin code is incorrect, check your pin and try again")

    GREETING, current_user = nav_greeting(request)
    return render(request, "bank/dashboard.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "account": account,
        "all_requests": REQUESTS,
        "transactions": TRANSACTION,
    	"payouts": total_payouts,
        "last_received": last_received,
        "all_cards": all_cards
    })

#Creating PIN
def create_pin_view(request):
    GREETING, current_user = nav_greeting(request)

    ERROR_MSG_LENGTH = ""
    ERROR_MSG_VALUE = ""
    # Checking if PIN has been created
    account = Account.objects.get(user=request.user)
    if account.pin_number:
        messages.error(
            request, "You have created your pin code already!")
        return redirect("dashboard")
    else:
        if request.method == "POST":
            pin_code1 = request.POST.get("pin-code1")
            pin_code2 = request.POST.get("pin-code2")
            if len(pin_code1) == 4 and pin_code1 == pin_code2:
                hashed_pin_code = make_password(pin_code1)
                account.pin_number = hashed_pin_code
                account.save()
                messages.success(
                request, "Your pin code has been created successfully!")
                return redirect("dashboard")
            elif len(pin_code1) != 4:
                ERROR_MSG_LENGTH = "Your pin must be four digits"
            
            elif pin_code1 != pin_code2:
                ERROR_MSG_VALUE = "The both PIN fields must match"

    return render(request, "bank/create_pin.html", {
        "error_length": ERROR_MSG_LENGTH,
        "error_value": ERROR_MSG_VALUE,
        "greeting": GREETING,
        "current_user": current_user
    })


#All Transactions Manager
def transaction_view(request):
    GREETING, current_user = nav_greeting(request)
    SEARCH_RESULT = None
    SEARCH_QUERY = ""

    #Search Section
    if "trans-search" in request.GET:
        SEARCH_QUERY = request.GET.get("trans-search")
        SEARCH_RESULT = Transaction.objects.filter(
            Q(receiver_account__account_name__icontains=SEARCH_QUERY) |
            Q(sender_account__account_name__icontains=SEARCH_QUERY) |
            Q(transaction_id__icontains=SEARCH_QUERY) |
            Q(description__icontains=SEARCH_QUERY) 
            )
    if "date-from" and "date-to" in request.GET:
        date_start = request.GET.get("date-from")
        date_end = request.GET.get("date-to")
        other_sort = request.GET.get("other-sort")
        print(date_start, date_end)

        SEARCH_RESULT = Transaction.objects.filter(
            date__gte=date_start, date__lte=date_end
        )

    account = Account.objects.get(user=request.user)
    #Transaction Section
    TRANSACTION = None
    try:
        TRANSACTION = Transaction.objects.filter(
                Q(sender_account=account) | Q(receiver_account=account)
        ).order_by("-date")

        custom_range, TRANSACTION = paginate_pages(
        request, TRANSACTION, results=10)
    except:
        TRANSACTION = None
    #End of transaction section

    return render(request, "bank/transactions.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "transactions": TRANSACTION,
        "account": account,
        "search_result": SEARCH_RESULT,
        "search_query": SEARCH_QUERY,
        "custom_range": custom_range,
    })


#Logic in charge of Account Profile
def account_view(request):
    GREETING, current_user = nav_greeting(request)
    account = Account.objects.get(user=request.user)
    user = request.user
    KYC_MODEL = None
    try:
        KYC_MODEL = KYC.objects.get(user=request.user)
    except:
        KYC_MODEL = None

    if request.method == "POST":
        new_photo = request.FILES.get("new-photo")
        old_password = request.POST.get("current-password")
        new_password = request.POST.get("new-password1")
        confirm_password = request.POST.get("new-password2")
        user_instance = User.objects.get(id=request.user.id)
        if new_photo:
            account.account_image = new_photo
            account.save()
            messages.success(request, "You have successfully changed your profile picture")
        elif old_password and new_password and confirm_password:
            if new_password == confirm_password:
                password = user_instance.password
                hashed_new_password = make_password(password)
                password = hashed_new_password
                user_instance.save()
                # Update the session with the user's current password
                update_session_auth_hash(request, request.user)
                messages.success(request, "You have successfully changed your password")
            else:
                messages.error(request, "The new password field and old password field must match")

        return redirect("account")
            
    return render(request, "bank/account.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "account": account,
        "kyc": KYC_MODEL,
        "user": user
    })


def delete_account(request):
    user = User.objects.get(id=request.user.id)
    account = Account.objects.get(user=request.user)

    #Delete logged in user and account
    user.delete()
    account.delete()

    messages.success(request, "You have successfully deleted your account!")
    return redirect("home")


def notification_view(request):
    GREETING, current_user = nav_greeting(request)
    NOTIFICATIONS = None
    user_transactions = Transaction.objects.filter(sender=request.user).order_by("date").all()
    account = Account.objects.get(user=request.user)

    try:
        notifications = Notification.objects.filter(user=request.user)
        all_trans_id = [noti.transaction.transaction_id for noti in notifications]
    except:
        notifications = None
        all_trans_id = []

    #Create A Notification

    for trans in user_transactions:
        sender_account = trans.sender_account
        receiver_account = trans.receiver_account
        amount = trans.amount
        trans_type = trans.tranaction_type
        trans_id = trans.transaction_id

        if trans_id not in all_trans_id:
            # Notification for cash transfer
            if sender_account == account and trans_type == "cash_transfer":
                message = f"You have transferred N{amount} to {receiver_account.account_name}"
                new_notification = Notification.objects.create(
                    user = request.user,
                    message=message,
                    notification_type = "cash_transfer",
                    transaction = trans
                )
                new_notification.save()

            # Notification for cash received
            elif receiver_account == account and trans_type == "cash_transfer":
                message = f"You have received N{amount} from {sender_account.account_name}"
                new_notification = Notification.objects.create(
                    user = request.user,
                    message=message,
                    notification_type = "cash_received",
                    transaction = trans

                )
                new_notification.save()

            # Notification for paid request
            elif sender_account == account and trans_type == "paid_request":
                message = f"You have paid a request of N{amount} to {receiver_account.account_name}"
                new_notification = Notification.objects.create(
                    user = request.user,
                    message=message,
                    notification_type="paid_request",
                    transaction=trans
                )
                new_notification.save()

            # Notification for payment received
            elif receiver_account == account and trans_type == "paid_request":
                message = f"You have received a payment of N{amount} from {sender_account.account_name}"
                new_notification = Notification.objects.create(
                    user = request.user,
                    message=message,
                    notification_type="payment_received",
                    transaction=trans
                )
                new_notification.save()

    try:
        NOTIFICATIONS = Notification.objects.filter(user=request.user).order_by("-date")
    except:
        NOTIFICATIONS = None


    return render(request, "bank/notifications.html", {
        "greeting": GREETING,
        "current_user": current_user,
        "notifications": NOTIFICATIONS
    })




#File Download in Payment requests logic
class FileDownloadView1(View):
    def get(self, request, req_id):
        payment_request = PaymentRequest.objects.get(request_id=req_id)
        file_path = payment_request.proof_doc1.path
        file_name = payment_request.proof_doc1.name

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'

        return response
    
class FileDownloadView2(View):
    def get(self, request, req_id):
        payment_request = PaymentRequest.objects.get(request_id=req_id)
        file_path = payment_request.proof_doc2.path
        file_name = payment_request.proof_doc2.name

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'

        return response
    
class FileDownloadView3(View):
    def get(self, request, req_id):
        payment_request = PaymentRequest.objects.get(request_id=req_id)
        file_path = payment_request.proof_doc3.path
        file_name = payment_request.proof_doc3.name

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'

        return response


def render_to_pdf(request, template_path, context_dict):
    template = get_template("bank/bank_statement.html")
    account = Account.objects.get(user=request.user)
    html = template.render(
        {
            "account": account,
        }
    )
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="your_pdf_file.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error rendering PDF', status=500)

    return response


def html_to_pdf(request):
    template_path = 'bank/bank_statement.html'
    account = Account.objects.get(user=request.user)
    context_dict = {
        "account": account,
    }  # Add your context data here

    return render_to_pdf(request, template_path, context_dict)



