from django.shortcuts import render
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentRequestSerializer, FundTransferRequestSerializer, GetBalanceRequestSerializer
from .models import Beneficiary, FundTransferTransaction,TransactionConfig
from .services import transaction_process_imps,get_transaction_status, get_auth_tokens, DynamicIVJce
from rest_framework.decorators import api_view,permission_classes 
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
import uuid
from .permissions import IsAuthorizedIP, IsSuperUser
import json
import ast
import requests
from django.http import JsonResponse
from .services import fetch_bank_balance
from .permissions import is_authorized_ip
from django.contrib.auth import get_user

class FundTransferAPIView(APIView):
    """
    Fund Transfer API (IMPS / NEFT / RTGS)
    """
    permission_classes = [IsAuthorizedIP]
    def post(self, request, *args, **kwargs):
        # pdb.set_trace()
        import sys
        print("RAW BODY:", request.body.decode('utf-8', errors='replace'), file=sys.stderr)
        raw_body = request.body.decode('utf-8', errors='replace')
        print("RAW BODY:", raw_body, file=sys.stderr)
        clean_body = raw_body.replace('\xa0', ' ').strip()
        print("Content-Type:", request.content_type)
        print("Request Body:", request.body.decode('utf-8', errors='replace'))
        print("Request Data:", request.data)

        try:
            data = json.loads(clean_body)
        except json.JSONDecodeError as e:
            print({"error": f"Invalid JSON: {str(e)}"})


        try:
            serializer = FundTransferRequestSerializer(data=request.data)
        except Exception as e:
            import traceback; traceback.print_exc();
            pdb.set_trace()

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

import pdb
class TransactionStatusAPIView(APIView):
    """
    Transaction Status API
    """
    permission_classes = [IsAuthorizedIP]

    def post(self, request, *args, **kwargs):
        transaction_id = request.data.get('transactionReferenceNumber')
        if not transaction_id:
            return Response({"error": "Transaction ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = FundTransferTransaction.objects.get(transaction_reference_no=transaction_id)
            transaction_status = transaction.txn_status
                # pdb.set_trace()
            if transaction_status == "INITIATED":
                service_response = get_transaction_status(transaction)
                return Response(service_response, status=status.HTTP_200_OK)
            else:
                response_data = transaction.response_data
                # pdb.set_trace()
                if response_data:
                    try:
                        response_data = json.loads(response_data)
                    except:
                        response_data = ast.literal_eval(response_data)

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "No response data available."}, status=status.HTTP_404_NOT_FOUND)

        except FundTransferTransaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
def Get_balance_view(request):
 
    user = get_user(request)

    if user.is_authenticated and user.is_superuser:
        pass
    elif is_authorized_ip(request):
        pass  
    else:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    try:
        balance_data = fetch_bank_balance()
        return JsonResponse(balance_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# @api_view(['GET'])
# @permission_classes([IsSuperUser, IsAuthorizedIP])
# def Get_balance_view(request):
#     """
#     Only Admin + Authorized IP can access this
#     """
#     try:
#         balance_data = fetch_bank_balance()  # your existing logic
#         return Response(balance_data)
#     except Exception as e:
#         return Response({'error': str(e)}, status=500)
