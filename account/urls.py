from django.urls import path
from . import views
from . import transfer_manager
from . import receive_manager


urlpatterns = [
    # Dashboard
    path("dashboard", views.dashboard_view, name="dashboard"),

    # Transfer
    path("transfer", transfer_manager.transfer_start_view, name="transfer1"),
    path("transfer/<account_number>", transfer_manager.initiate_transfer, name="transfer2"),
    path("transfer/<account_number>/<trans_number>", transfer_manager.process_transfer, name="transfer3"),
    path("transfer-success/<account_number>/<trans_number>", transfer_manager.transfer_success, name="transfer-success"),

    #Receive
    path("receive", receive_manager.request_start_view, name="receive1"),
    path("receive/<account_number>", receive_manager.initiate_request, name="receive2"),
    path("receive/<account_number>/<request_id>",
         receive_manager.process_request, name="receive3"),
    path("request-success/<account_number>/<request_id>",
         receive_manager.request_success, name="request-success"),

    # Payment Requests
    path("payment-requests", receive_manager.request_clearing_house, name="request"),

    #Transactions
    path("transactions", views.transaction_view, name="transaction"),

    #Account
    path("account", views.account_view, name="account"),

    #Delete Account
    path("account/delete-account", views.delete_account, name="delete-account"),

    #KYC
    path("kyc-form", views.kyc_view, name="kyc"),

    #Create PIN
    path("create-pin", views.create_pin_view, name="create-pin"),
    
    #Notification
    path("notifications", views.notification_view, name="notification"),

    #Html to pdf
    path("bank-statement", views.html_to_pdf, name="bank-statement"),

    #Download request proof
    path('download/proof1/<req_id>/', views.FileDownloadView1.as_view(), name='file_download1'),
    path('download/proof2/<req_id>/', views.FileDownloadView2.as_view(), name='file_download2'),
    path('download/proof3/<req_id>/', views.FileDownloadView3.as_view(), name='file_download3'),
]
