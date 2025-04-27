from django.shortcuts import render
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentRequestSerializer, FundTransferRequestSerializer
from .models import Beneficiary, FundTransferTransaction,TransactionConfig
from .services import transaction_process_imps
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid
from .permissions import IsAuthorizedIP

class FundTransferAPIView(APIView):
    """
    Fund Transfer API (IMPS / NEFT / RTGS)
    """
    permission_classes = [IsAuthorizedIP]
    def post(self, request, *args, **kwargs):
        serializer = FundTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                config = TransactionConfig.objects.first()
                if not config:
                    return Response({"error": "Transaction Config not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                data = serializer.validated_data
                beneficiary_data = data.get('beneficiary')
                amount = data.get('amount')
                payment_description = data.get('payment_description', "")
                transaction_type = data.get('transaction_type', 'IMPS')

                # Get or create Beneficiary
                beneficiary, _ = Beneficiary.objects.get_or_create(
                    account_number=beneficiary_data.get("beneficiary_account"),
                    ifsc_code=beneficiary_data.get("beneficiary_ifsc"),
                    defaults={
                        "name": beneficiary_data.get("beneficiary_name", "Unnamed"),
                        "address": beneficiary_data.get("address", ""),
                        "email_id": beneficiary_data.get("email_id", "abc@gmail.com"),
                        "mobile_no": beneficiary_data.get("mobile_no", "9999999999"),
                    },
                )
                beneficiary.save()

                # Save initial transaction
                transaction = FundTransferTransaction.objects.create(
                    beneficiary=beneficiary,
                    debit_account_number=config.debit_account_number,
                    remitter_name=config.remitter_name,
                    amount=str(amount),
                    currency="INR",
                    transaction_type=transaction_type,
                    payment_description=payment_description,
                    txn_status="INITIATED",
                    txn_received_timestamp=timezone.now(),
                    transaction_reference_no=str(uuid.uuid4()).replace("-", "")[:16]
                )
                transaction.save()

                # Process fund transfer
                # service_response = process_fund_transfer(transaction, config)
                service_response = transaction_process_imps(transaction)
                if service_response.get("error"):
                    return Response(service_response, status=500)
                return Response(service_response, status=200)


            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
