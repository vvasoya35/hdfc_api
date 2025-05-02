from django.shortcuts import render
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentRequestSerializer, FundTransferRequestSerializer, GetBalanceRequestSerializer, GetBankStatementRequestSerializer
from .models import Beneficiary, FundTransferTransaction,TransactionConfig
from .services import get_statement, transaction_process_imps,get_transaction_status, get_auth_tokens, DynamicIVJce
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

        import sys
        # print("RAW BODY:", request.body.decode('utf-8', errors='replace'), file=sys.stderr)
        raw_body = request.body.decode('utf-8', errors='replace')
        # print("RAW BODY:", raw_body, file=sys.stderr)
        clean_body = raw_body.replace('\xa0', ' ').strip()
        # print("Content-Type:", request.content_type)
        # print("Request Body:", request.body.decode('utf-8', errors='replace'))
        # print("Request Data:", request.data)

        try:
            data = json.loads(clean_body)
        except json.JSONDecodeError as e:
            print({"error": f"Invalid JSON: {str(e)}"})


        try:
            serializer = FundTransferRequestSerializer(data=request.data)
        except Exception as e:
            import traceback; traceback.print_exc();

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

class TransactionStatusAPIView(APIView):
    """
    Transaction Status API
    """
    permission_classes = [IsAuthorizedIP]

    def post(self, request, *args, **kwargs):
        transaction_id = request.data.get('transactionReferenceNumber', None)
        transaction_type = request.data.get('transactionType', None)
        transactionDate = request.data.get('transactionDate', None)
        if not transaction_id:
            
            return Response({"error": "transactionReferenceNumber is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = FundTransferTransaction.objects.get(transaction_reference_no=transaction_id)
            transaction_status = transaction.txn_status
            # if transaction is None:
            if transaction:
                if not transaction_id or not transaction_type or not transactionDate:
                    return Response({"error": "transactionReferenceNumber, transactionType and transactionDate are required."}, status=status.HTTP_400_BAD_REQUEST)
                
                service_response = get_transaction_status(transaction_id,transaction_type, transactionDate)
                return Response(service_response, status=status.HTTP_200_OK)


            if transaction_status == "INITIATED":
                service_response = get_transaction_status(transaction)
                return Response(service_response, status=status.HTTP_200_OK)
            else:
                response_data = transaction.response_data

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

class SatatementAPIView(APIView):
    """
    Bank Statement API
    """
    permission_classes = [IsAuthorizedIP]

    def post(self, request, *args, **kwargs):
        # Implement your logic here
        serializer = GetBankStatementRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Process the request data
            # For example, you can fetch the bank statement based on the provided parameters
            start_date = serializer.validated_data.get('fromDate').strftime("%d/%m/%Y")
            end_date = serializer.validated_data.get('toDate').strftime("%d/%m/%Y")
            numberOfTransactions = serializer.validated_data.get('numberOfTransactions')
            promt = serializer.validated_data.get('prompt', "")
            
            # Call the function to get the bank statement
            bank_statement = get_statement(start_date, end_date, numberOfTransactions, promt)
            return Response(bank_statement, status=status.HTTP_200_OK)
        return Response({"message": "Bank Statement API"}) 

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
