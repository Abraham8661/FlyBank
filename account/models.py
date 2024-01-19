from django.db import models
from users_auth.models import User
import uuid
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import post_save
    

ACCOUNT_STATUS = (
    ("active", "Active"),
    ("inactive", "Inactive")
)

KYC_STATUS = (
    ("not_submitted", "Not Submitted"),
    ("in_review", "In Review"),
    ("approved", "Approved"),
    ("not_approved", "Not Approved")
)

TRANS_STATUS = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("completed", "Completed"),
    ("Failed", "Failed"),
    ("Cancelled", "Cancelled"),
    ("refunded", "Refunded"),
)

TRANS_TYPE = (
    ("cash_transfer", "Cash Transfer"),
    ("cash_received", "Cash Received"),
    ("paid_request", "Paid Request"),
    ("payment_received", "Payment Received"),
    ("card_purchase", "Card Purchase"),
    ("card_funding", "Card Funding"),
    ("card_withdrawal", "Card Withdrawal"),
)

RECENT_TYPE = (
    ("cash_transfer", "Cash Transfer"),
    ("paid_request", "Paid Request"),
)


GENDER = (
    ("male", "Male"),
    ("female", "Female")
)

IDENTITY_DOC = (
    ("voters_card", "Voters Card"),
    ("national_identity_card", "National Identity Card"),
    ("international_passport", "International Passport"),
    ("others", "Others"),
)

STATUS = (
    ("settled", "Settled"),
    ("cancelled", "Cancelled"),
    ("processing", "Processing"),
    ("request", "Request"),
    ("declined", "Declined"),
)

CARD_TYPE = (
    ("visa", "VISA"),
    ("master", "MASTER"),
    ("verve", "VERVE"),
)


class Account(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = ShortUUIDField(
        unique=True, length=7, max_length=10, prefix="024", alphabet="1234567890")
    account_balance = models.FloatField(default=0.00)
    account_id = ShortUUIDField(
        unique=True, length=4, max_length=7, prefix="FBN", alphabet="1234567890")
    pin_number = models.CharField(max_length=500, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True)
    account_name = models.CharField(max_length=100, null=True)
    account_image = models.ImageField(upload_to="account", null=True)
    account_status = models.CharField(
        max_length=100, choices=ACCOUNT_STATUS, default="inactive")
    date = models.DateTimeField(auto_now_add=True)
    recommended_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="referral")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        try:
            return f"{self.user}"
        except:
            return "Account Model"


class KYC(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account = models.OneToOneField(Account, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    address = models.TextField(max_length=800)
    date_of_birth = models.DateTimeField(auto_now_add=False)
    gender = models.CharField(choices=GENDER, max_length=50)
    identity_document = models.CharField(choices=IDENTITY_DOC, max_length=50)
    identity_image_front = models.ImageField(upload_to="kyc")
    identity_image_back = models.ImageField(upload_to="kyc")
    signature = models.ImageField(upload_to="kyc")
    passport = models.ImageField(upload_to="kyc")
    kyc_status = models.CharField(
        max_length=100, choices=KYC_STATUS, default="not_submitted")
    date = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        try:
            return f"{self.first_name} {self.last_name}"
        except:
            return "KYC Model"
        
    class Meta:
        ordering = ["-date"]
    

def create_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

def save_account(sender, instance, **kwargs):
    instance.account.save()

post_save.connect(create_account, sender=User)
post_save.connect(save_account, sender=User) 


class ChargeManager(models.Model):
    id = models.UUIDField(primary_key=True, unique=True,
                          editable=False, default=uuid.uuid4)
    charge_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="FEE", alphabet="1234567890")
    transaction_type = models.CharField(max_length=500)
    fee = models.FloatField(default=0.00)
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        return self.transaction_type
    


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    transaction_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="TRN", alphabet="1234567890")

    sender = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    sender_account = models.ForeignKey(Account, on_delete=models.DO_NOTHING, null=True, blank=True)
    receiver_account = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, null=True, blank=False, related_name="recipient")
    
    description = models.CharField(max_length=500)

    amount = models.FloatField(default=0.00)
    transaction_fee = models.ForeignKey(ChargeManager, on_delete=models.DO_NOTHING, null=True)

    status = models.CharField(
        max_length=100, choices=TRANS_STATUS)
    tranaction_type = models.CharField(
        max_length=100, choices=TRANS_TYPE, null=True)
    
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        return self.transaction_id
    
    class Meta:
        ordering = ["-date"]
    

class PaymentRequest(models.Model):
    id = models.UUIDField(primary_key=True, unique=True,
                          editable=False, default=uuid.uuid4)
    request_id = ShortUUIDField(
        unique=True, length=10, max_length=20, prefix="RQ", alphabet="1234567890")

    sender = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    sender_account = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, null=True, blank=True)
    receiver_account = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, null=True, blank=False, related_name="receiver")

    description = models.CharField(max_length=500)

    payment_due_by = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    amount = models.FloatField(default=0.00)
    status = models.CharField(
        max_length=100, choices=STATUS, null=True)

    proof_doc1 = models.FileField(upload_to="request", null=True, blank=True)
    proof_doc2 = models.FileField(upload_to="request", null=True, blank=True)
    proof_doc3 = models.FileField(upload_to="request", null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        return self.request_id
    
    class Meta:
        ordering = ["-date"]


class UserRecentManager(models.Model):
    id = models.UUIDField(primary_key=True, unique=True,
                          editable=False, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    transaction_accounts = models.ManyToManyField(Account)
    request_accounts = models.ManyToManyField(Account, related_name="request_account")
    recent_type = models.CharField(
        max_length=100, choices=RECENT_TYPE, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"
    
    class Meta:
        ordering = ["-date"]


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, unique=True,
                          editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=1500, null=False)
    date = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length=100, choices=TRANS_TYPE, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return f"{self.user}"
    
    class Meta:
        ordering = ["-date"]
    

class CreditCard(models.Model):
    id = models.UUIDField(primary_key=True, unique=True,
                          editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, null=True, blank=True)
    card_code = ShortUUIDField(
        unique=True, length=5, max_length=7, prefix="CR", alphabet="1234567890")
    card_balance = models.FloatField(default=0.00)
    card_type = models.CharField(
        max_length=100, choices=CARD_TYPE, null=False)
    card_name = models.CharField(max_length=500)
    card_number = ShortUUIDField(
        unique=True, length=18, max_length=18, prefix="85", alphabet="1234567890")
    CVV = ShortUUIDField(
        unique=True, length=3, max_length=3, alphabet="1234567890")
    issue_date = models.DateTimeField(auto_now_add=False)
    expiry_date = models.DateTimeField(auto_now_add=False)
    date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.account.account_name}"
    
    class Meta:
        ordering = ["-date"]
    

