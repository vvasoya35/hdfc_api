from django.shortcuts import render
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentRequestSerializer, FundTransferRequestSerializer, GetBalanceRequestSerializer
from .models import Beneficiary, FundTransferTransaction,TransactionConfig
from .services import transaction_process_imps,get_transaction_status, get_auth_tokens, DynamicIVJce
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid
from .permissions import IsAuthorizedIP
import json
import ast
import requests
from django.http import JsonResponse
from .services import fetch_bank_balance



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


def Get_balance_view(request):
    balance = fetch_bank_balance()
    return JsonResponse(balance, safe=False)


# def Get_balance_view(request):
#     get_balsnce_url = "https://apiext.uat.idfcfirstbank.com/acctenq/v2/prefetchAccount"
#     config = TransactionConfig.objects.first()
#     get_payload = {
#             "prefetchAccountReq": {
#                 "CBSTellerBranch": "",
#                 "CBSTellerID": "",
#                 "accountNumber": config.debit_account_number
#             }
#         }
#     data = json.dumps(get_payload)  # ✔️ convert dict to JSON string
#     secret_hex_key = config.secret_hex_key
#     encrypted = DynamicIVJce.encrypt(data, secret_hex_key) 
#     access_token = get_auth_tokens()
#     if access_token:
#         headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/x-www-form-urlencoded",
#         "source": "KAC",
#         "correlationId" : "523134453sadaazd",
#         "Content-Type":"application/octet-stream"
#         }
#     encrypted_payload =  encrypted

#     fund_t_response = requests.post(get_balsnce_url, headers=headers, data=encrypted_payload.encode("utf-8"))

#     encrypted_payload = fund_t_response.text

#     decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)
#     decrypted_json = json.loads(decrypted)
#     return JsonResponse(decrypted_json, safe=False)
