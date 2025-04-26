from rest_framework import serializers
from .models import Beneficiary, FundTransferTransaction

class PaymentRequestSerializer(serializers.Serializer):
    beneficiary_name = serializers.CharField(required=False, allow_blank=True)
    beneficiary_account_number = serializers.CharField()
    beneficiary_ifsc_code = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    remark = serializers.CharField(required=False, allow_blank=True)
