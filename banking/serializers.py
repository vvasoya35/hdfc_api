from rest_framework import serializers
from .models import Beneficiary, FundTransferTransaction

class PaymentRequestSerializer(serializers.Serializer):
    beneficiary_name = serializers.CharField(required=False, allow_blank=True)
    beneficiary_account_number = serializers.CharField()
    beneficiary_ifsc_code = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    remark = serializers.CharField(required=False, allow_blank=True)


class BeneficiarySerializer(serializers.ModelSerializer):
    beneficiary_account = serializers.CharField(required=True)
    beneficiary_ifsc = serializers.CharField(required=True)
    beneficiary_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email_id = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    mobile_no = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Beneficiary
        fields = ['beneficiary_name', 'beneficiary_account', 'beneficiary_ifsc', 'address', 'email_id', 'mobile_no']


class FundTransferRequestSerializer(serializers.Serializer):
    beneficiary = BeneficiarySerializer()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_description = serializers.CharField(required=False, allow_blank=True)
    # transaction_type = serializers.ChoiceField(choices=[('IMPS', 'IMPS'), ('NEFT', 'NEFT'), ('RTGS', 'RTGS')], default='IMPS', required=False)

class GetBalanceRequestSerializer(serializers.Serializer):
    transactionReferenceNumber = serializers.CharField(required=True)

class GetBankStatementRequestSerializer(serializers.Serializer):
    "fromDate" = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y"])
    "toDate" = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y"])
    "numberOfTransactions" = serializers.IntegerField()
    "prompt" = serializers.CharField(required=False, allow_blank=True, allow_null=True)