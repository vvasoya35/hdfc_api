from django.shortcuts import render
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentRequestSerializer
from .models import Beneficiary, FundTransferTransaction,TransactionConfig
from .services import initiate_fund_transfer
from rest_framework.decorators import api_view


class ProcessPaymentAPIView(APIView):
    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        if serializer.is_valid():
            config = TransactionConfig.objects.first()
            data = serializer.validated_data

            # Check if Beneficiary exists
            beneficiary, created = Beneficiary.objects.get_or_create(
                account_number=data['beneficiary_account_number'],
                ifsc_code=data['beneficiary_ifsc_code'],
                defaults={
                    'name': data.get('beneficiary_name', ''),
                }
            )

            transaction = FundTransferTransaction.objects.create(
                beneficiary=beneficiary,
                debit_account_number=config.debit_account_number,  # You can dynamically set your own logic here
                remitter_name=config.remitter_name,    # Your default sender name
                amount=data['amount'],
                payment_description=data.get('remark', ''),
            )

            return Response({
                "message": "Transaction created successfully",
                "transaction_id": transaction.id,
                "transaction_unique_id": str(transaction.unique_id),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# views.py


@api_view(['POST'])
def fund_transfer_view(request):
    data = request.data
    beneficiary_name = data.get('beneficiary_name')
    beneficiary_account = data.get('beneficiary_account')
    beneficiary_ifsc = data.get('beneficiary_ifsc')
    amount = data.get('amount')
    remark = data.get('remark')

    result = initiate_fund_transfer(
        beneficiary_name=beneficiary_name,
        beneficiary_account=beneficiary_account,
        beneficiary_ifsc=beneficiary_ifsc,
        amount=amount,
        remark=remark
    )

    return Response({
        "status": "Success",
        "bank_response": result
    })
