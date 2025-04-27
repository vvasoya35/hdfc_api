from .models import TransactionConfig
from .utils import generate_unique_jti, get_future_unix_time_ist, DynamicIVJce
import json
import requests
import uuid
import jwt
from django.utils import timezone
import pdb 

def get_auth_tokens():
    config = TransactionConfig.objects.first()
    private_key = config.private_key.replace('\\n', '\n')
    client_id = config.client_id
    kid = config.kid
    sub = config.sub
    iss = config.iss
    aud = config.aud

    header = {
    "alg": "RS256",
    "typ": "JWT",
    "kid": kid
    }

    # JWT payload (you can add more custom fields)
    payload = {
    "jti":generate_unique_jti(),
    "sub":sub,
    "iss":iss,
    "aud":aud, 
    "exp":get_future_unix_time_ist()
    }

    token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)

    authorized_payload = {
        "grant_type":"client_credentials",
        "scope":"paymenttxn-v1fundTransfer paymentenq-paymentTransactionStatus cbs-acctenq-accountBalance cbs-acctenq-accountStatement",
        "client_id":client_id,
        "client_assertion_type":"urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion":token
    }

    auth_url = "https://apiext.uat.idfcfirstbank.com/authorization/oauth2/token?"

    auth_res = requests.post(auth_url, data=authorized_payload)
    if auth_res.status_code == 200:
        access_token = auth_res.json()['access_token']
        return access_token
    else:
        print("Error fetching access token:", auth_res.status_code, auth_res.text)
        return None

def transaction_process_imps(transaction):
    # transaction
    config = TransactionConfig.objects.first()
    t_payload = {
        "initiateAuthGenericFundTransferAPIReq": {
            "tellerBranch": "",
            "tellerID": "",
            # "transactionID": "87276667871",
            "transactionID": transaction.transaction_id,
            "debitAccountNumber": transaction.debit_account_number,
            "creditAccountNumber": transaction.beneficiary.account_number,
            "remitterName": transaction.remitter_name,
            "amount": str(transaction.amount),
            "currency": "INR",
            "transactionType": "IMPS",
            "paymentDescription": transaction.payment_description,
            "beneficiaryIFSC": transaction.beneficiary.ifsc_code,
            "beneficiaryName": transaction.beneficiary.name,
            "beneficiaryAddress": "",
            "emailId":"abc@gmail.com",
            "mobileNo": "9999999999"
        }
    }

    data = json.dumps(t_payload)  
    secret_hex_key = config.secret_hex_key

    encrypted = DynamicIVJce.encrypt(data, secret_hex_key)  
    if encrypted:
        print("Encrypted Payload:")
        # print(encrypted)
        access_token = get_auth_tokens()
        if access_token:
            headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "source": "KAC",
            "correlationId" : "523134453sadaazd",
            "Content-Type":"application/octet-stream"
            }
            encrypted_payload =  encrypted

            fund_transfer_url = "https://apiext.uat.idfcfirstbank.com/paymenttxns/v1/fundTransfer"

            fund_t_response = requests.post(fund_transfer_url, headers=headers, data=encrypted_payload.encode("utf-8"))

            encrypted_payload = fund_t_response.text
            # pdb.set_trace()
            decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)
            if decrypted:
                print("Decrypted Payload:")
                # print(decrypted)

                result = json.loads(decrypted)
                transaction.response_data = result
                transaction.http_status_code = fund_t_response.status_code
                transaction.txn_updated_timestamp = timezone.now()
                transaction.txn_received_timestamp = result['initiateAuthGenericFundTransferAPIResp']['metaData']['time']
                transaction.message_type = result['initiateAuthGenericFundTransferAPIResp']['metaData']['message']
                if result['initiateAuthGenericFundTransferAPIResp']['metaData']['status'] == "ERROR":
                    transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['metaData']['status']
                else:
                    transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['resourceData']['status']
                    transaction.transaction_reference_no = result['initiateAuthGenericFundTransferAPIResp']['resourceData']['transactionReferenceNo']
                transaction.save()
                return result
            else:
                print("Decryption failed.")
                return {"error": "Decryption failed."}
            
        else:
            print("Failed to get access token.")
            return {"error": "Failed to get access token."}
    else:
        print("Encryption failed.")
        return {"error": "Encryption failed."}
