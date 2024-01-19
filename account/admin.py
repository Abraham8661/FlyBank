from django.contrib import admin
from .models import Account, KYC, Transaction, ChargeManager, PaymentRequest, UserRecentManager, Notification, CreditCard
# Register your models here.


admin.site.register(Account)
admin.site.register(KYC)
admin.site.register(Transaction)
admin.site.register(PaymentRequest)
admin.site.register(ChargeManager)
admin.site.register(UserRecentManager)
admin.site.register(Notification)
admin.site.register(CreditCard)
