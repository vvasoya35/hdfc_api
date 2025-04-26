from .models import TransactionConfig
from .utils import generate_unique_jti, get_future_unix_time_ist, DynamicIVJce
import json
import requests
import uuid
import jwt

def generate_jwt_and_access_token():
    config = TransactionConfig.objects.first()

    private_key = config.private_key
    client_id = config.client_id
    kid = config.kid
    sub = config.sub
    iss = config.iss
    aud = config.aud

    # JWT Header
    headers = {
        "alg": "RS256",
        "typ": "JWT",
        "kid": kid
    }

    # JWT Payload
    payload = {
        "jti": generate_unique_jti(),
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": get_future_unix_time_ist()
    }

    # Encode
    token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

    # Request Access Token
    authorized_payload = {
        "grant_type": "client_credentials",
        "scope": "paymenttxn-v1fundTransfer paymentenq-paymentTransactionStatus cbs-acctenq-accountBalance cbs-acctenq-accountStatement",
        "client_id": client_id,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": token
    }

    auth_url = config.aud  # or your auth url

    auth_res = requests.post(auth_url, data=authorized_payload)
    access_token = auth_res.json().get('access_token')
    return access_token

def initiate_fund_transfer(beneficiary_name, beneficiary_account, beneficiary_ifsc, amount, remark):
    config = TransactionConfig.objects.first()

    # Step 1: Get Access Token
    access_token = generate_jwt_and_access_token()

    # Step 2: Prepare Transaction Payload
    txn_id = str(uuid.uuid4()).replace('-', '')[:12]
    t_payload = {
        "initiateAuthGenericFundTransferAPIReq": {
            "tellerBranch": "",
            "tellerID": "",
            "transactionID": txn_id,
            "debitAccountNumber": config.debit_account_number,
            "creditAccountNumber": beneficiary_account,
            "remitterName": config.remitter_name,
            "amount": str(amount),
            "currency": "INR",
            "transactionType": "NEFT",
            "paymentDescription": remark,
            "beneficiaryIFSC": beneficiary_ifsc,
            "beneficiaryName": beneficiary_name,
            "beneficiaryAddress": "",
            "emailId": "abc@gmail.com",
            "mobileNo": "9999999999"
        }
    }

    # Step 3: Encrypt Payload
    payload_json = json.dumps(t_payload)
    encrypted_payload = DynamicIVJce.encrypt(payload_json, config.secret_hex_key)

    # Step 4: API Call
    fund_transfer_url = "https://apiext.uat.idfcfirstbank.com/paymenttxns/v1/fundTransfer"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "source": "KAC",
        "correlationId": str(uuid.uuid4()),
        "Content-Type": "application/octet-stream"
    }

    response = requests.post(fund_transfer_url, headers=headers, data=encrypted_payload.encode('utf-8'))

    # Step 5: Decrypt Response
    encrypted_response = response.text
    decrypted_response = DynamicIVJce.decrypt(encrypted_response, config.secret_hex_key)

    return decrypted_response
