# urls.py
from django.urls import path
from .views import FundTransferAPIView

urlpatterns = [
    # path('process-payment/', ProcessPaymentAPIView.as_view(), name='process-payment'),
    # # path('fund-transfer/', fund_transfer_view, name='fund_transfer'),
    # path('api/imps-transfer/', imps_fund_transfer_view, name='imps_transfer'),    
    path('fund-transfer/', FundTransferAPIView.as_view(), name='fund_transfer'),

]
