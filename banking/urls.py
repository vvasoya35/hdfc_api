# urls.py
from django.urls import path
from .views import FundTransferAPIView,TransactionStatusAPIView, Get_balance_user_view

urlpatterns = [
    # path('process-payment/', ProcessPaymentAPIView.as_view(), name='process-payment'),
    # # path('fund-transfer/', fund_transfer_view, name='fund_transfer'),
    # path('api/imps-transfer/', imps_fund_transfer_view, name='imps_transfer'),    
    path('fund-transfer/', FundTransferAPIView.as_view(), name='fund_transfer'),
    path('fund-status/', TransactionStatusAPIView.as_view(), name='fund_status'),
    path('user-api/get-balance/', Get_balance_user_view, name='user-get-balance'),
]
