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
    # "sub":"13a738f6-f2f6-4ca9-8d5c-40d67056da5e",
    # "iss":"13a738f6-f2f6-4ca9-8d5c-40d67056da5e",
    # "aud":"https://app.my.idfcfirstbank.com/platform/oauth/oauth2/token", 
    "exp":get_future_unix_time_ist()
    }

    token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)

    authorized_payload = {
        "grant_type":"client_credentials",
        "scope":"paymenttxn-v1fundTransfer paymentenq-paymentTransactionStatus cbs-acctenq-accountBalance cbs-acctenq-accountStatement",
        "client_id":client_id,
        # "client_id":"13a738f6-f2f6-4ca9-8d5c-40d67056da5e",
        "client_assertion_type":"urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion":token
    }

    # auth_url = "https://apiext.idfcfirstbank.com/authorization/oauth2/token"
    auth_url = config.auth_url
    auth_res = requests.post(auth_url, data=authorized_payload, timeout=10, verify=False)
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
            "source": config.source,
            "correlationId" : "523134453sadaazd",
            "Content-Type":"application/octet-stream"
            }
            encrypted_payload =  encrypted

            # fund_transfer_url = "https://apiext.uat.idfcfirstbank.com/paymenttxns/v1/fundTransfer"
            fund_transfer_url = config.fund_transfer_url
            fund_t_response = requests.post(fund_transfer_url, headers=headers, data=encrypted_payload.encode("utf-8"))

            encrypted_payload = fund_t_response.text

            decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)
            if decrypted:
                print("Decrypted Payload:")
                # print(decrypted)

                result = json.loads(decrypted)
                transaction.response_data = result
                transaction.http_status_code = fund_t_response.status_code
                transaction.txn_updated_timestamp = timezone.now()
                transaction.txn_received_timestamp = result['initiateAuthGenericFundTransferAPIResp']['metaData']['time']
                transaction.payment_description = result['initiateAuthGenericFundTransferAPIResp']['metaData']['message']
                if result['initiateAuthGenericFundTransferAPIResp']['metaData']['status'] == "ERROR":
                    transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['metaData']['status']
                else:
                    transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['metaData']['status']
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


def get_transaction_status(transaction):
    # transaction_status = "https://apiext.uat.idfcfirstbank.com/paymentenqs/v1/paymentTransactionStatus"
    transaction_status = transaction.transaction_status_url
    transactionDate = transaction.created_at.strftime("%d%m%Y")
    transactionReferenceNumber = transaction.transaction_reference_no
    config = TransactionConfig.objects.first()
    secret_hex_key = config.secret_hex_key.replace('\\n', '\n')
    cs_paylod = {
        "paymentTransactionStatusReq":
                {
                    "tellerBranch":"",
                    "tellerID":"",
                    "transactionType":transaction.transaction_type,
                    "transactionReferenceNumber":transactionReferenceNumber,
                    "paymentReferenceNumber":"",
                    "transactionDate":transactionDate
                }
        }
    access_token = get_auth_tokens()
    if access_token:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "source": config.source,
            "correlationId" : "523134453sadaazd",
            "Content-Type":"application/octet-stream"
        }

        data = json.dumps(cs_paylod) 

        encrypted = DynamicIVJce.encrypt(data, secret_hex_key) 
        if encrypted:
            encrypted_payload = encrypted
            fund_t_response = requests.post(transaction_status, headers=headers, data=encrypted_payload.encode("utf-8"))

            fund_t_response = requests.post(transaction_status, headers=headers, data=encrypted_payload.encode("utf-8"))

            encrypted_payload = fund_t_response.text            

            decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)

            if decrypted:
                    print("Decrypted Payload:")
                    # print(decrypted)

                    result = json.loads(decrypted)

                    transaction.response_data = result
                    transaction.http_status_code = fund_t_response.status_code
                    transaction.txn_updated_timestamp = timezone.now()
                    transaction.txn_received_timestamp = result['paymentTransactionStatusResp']['metaData']['time']
                    transaction.payment_description = result['paymentTransactionStatusResp']['metaData']['message']
                    if result['paymentTransactionStatusResp']['metaData']['status'] == "ERROR":
                        transaction.txn_status = result['paymentTransactionStatusResp']['metaData']['status']
                    else:
                        transaction.txn_status = result['paymentTransactionStatusResp']['resourceData']['status']
                        transaction.transaction_reference_no = result['paymentTransactionStatusResp']['resourceData']['transactionReferenceNumber']
                    transaction.save()
                    return result
            else:
                    print("Decryption failed.")
                    return {"error": "Decryption failed."}
            
        else:
            print("Encryption failed.")
            return {"error": "Encryption failed."}
    else:
        print("Failed to get access token.")
        return {"error": "Failed to get access token."}

def get_statement(start_date, end_date, numberOfTransactions, promt):
    # statement_url = "https://apiext.uat.idfcfirstbank.com/acctenq/v2/accountStatement"
    config = TransactionConfig.objects.first()
    statement_url = config.statement_url
    account_number = config.debit_account_number
    secret_hex_key = config.secret_hex_key
    get_payload = {
        "getAccountStatementReq": {
            "CBSTellerBranch": "",
            "CBSTellerID": "",
            "accountNumber": account_number,
            "fromDate": start_date,
            "toDate": end_date,
            "numberOfTransactions": f"{numberOfTransactions}",
            "prompt": promt
        }
    }

    data = json.dumps(get_payload) 

    access_token = get_auth_tokens()
    if access_token:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "source": config.source,
            "correlationId" : "523134453sad-9aazd88",
            "Content-Type":"application/octet-stream"
            }
        encrypted = DynamicIVJce.encrypt(data, secret_hex_key) 
        if encrypted:
            encrypted_payload = encrypted
            fund_t_response = requests.post(statement_url, headers=headers, data=encrypted_payload.encode("utf-8"))

            encrypted_payload = fund_t_response.text            

            decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)

            if decrypted:
                    print("Decrypted Payload:")
                    # print(decrypted)

                    result = json.loads(decrypted)
                    return result
            else:
                    print("Decryption failed.")
                    return {"error": "Decryption failed."}
            
        else:
            print("Encryption failed.")
            return {"error": "Encryption failed."}
    else:
        print("Failed to get access token.")
        return {"error": "Failed to get access token."}

def fetch_bank_balance():
    # get_balance_url = "https://apiext.uat.idfcfirstbank.com/acctenq/v2/prefetchAccount"
    config = TransactionConfig.objects.first()
    get_balance_url = config.get_balance_url

    get_payload = {
        "prefetchAccountReq": {
            "CBSTellerBranch": "",
            "CBSTellerID": "",
            "accountNumber": config.debit_account_number
        }
    }
    data = json.dumps(get_payload)

    secret_hex_key = config.secret_hex_key
    encrypted = DynamicIVJce.encrypt(data, secret_hex_key) 

    access_token = get_auth_tokens()
    if access_token:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "source": "KAC",
            "correlationId" : "523134453sad-9aazd88",
            "Content-Type":"application/octet-stream"
            }
        fund_t_response = requests.post(get_balance_url, headers=headers, data=encrypted.encode("utf-8"))

        encrypted_payload = fund_t_response.text
        decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)
        decrypted_json = json.loads(decrypted)

        return decrypted_json

    else:
        raise Exception("Access token not found")

# from .models import TransactionConfig
# from .utils import generate_unique_jti, get_future_unix_time_ist, DynamicIVJce
# import json
# import requests
# import uuid
# import jwt
# from django.utils import timezone
# import pdb
# import socket
# import logging
# import urllib3
# import traceback

# # Setup logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     filename='/var/log/banking_api.log',
#     filemode='a'
# )
# logger = logging.getLogger(__name__)

# # Disable SSL warnings if verify=False is used (not recommended for production)
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# def diagnose_connection(url):
#     """Test basic connectivity to the URL's host"""
#     try:
#         host = url.split("//")[1].split("/")[0]
#         logger.info(f"Testing connection to {host}")
        
#         # Test DNS resolution
#         try:
#             ip = socket.gethostbyname(host)
#             logger.info(f"DNS Resolution successful. {host} resolves to {ip}")
#         except socket.gaierror as e:
#             logger.error(f"DNS Resolution failed: {str(e)}")
#             return False
            
#         # Test socket connection
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.settimeout(5)
#         result = s.connect_ex((host, 443))
#         s.close()
        
#         if result == 0:
#             logger.info(f"Socket connection to {host}:443 successful")
#             return True
#         else:
#             logger.error(f"Socket connection to {host}:443 failed with error code {result}")
#             return False
            
#     except Exception as e:
#         logger.error(f"Connection test failed: {str(e)}")
#         return False

# def get_auth_tokens():
#     try:
#         config = TransactionConfig.objects.first()
#         if not config:
#             logger.error("No TransactionConfig found in database")
#             return None
            
#         private_key = config.private_key.replace('\\n', '\n')
#         client_id = config.client_id
#         kid = config.kid
#         sub = config.sub
#         iss = config.iss
#         aud = config.aud
#         auth_url = config.auth_url
        
#         logger.info(f"Attempting to get auth token from: {auth_url}")
        
#         # Test connectivity first
#         if not diagnose_connection(auth_url):
#             logger.error(f"Cannot establish connection to {auth_url}")
#             return None

#         header = {
#             "alg": "RS256",
#             "typ": "JWT",
#             "kid": kid
#         }

#         payload = {
#             "jti": generate_unique_jti(),
#             "sub": sub,
#             "iss": iss,
#             "aud": aud, 
#             "exp": get_future_unix_time_ist()
#         }

#         token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
        
#         logger.debug("JWT token generated successfully")

#         authorized_payload = {
#             "grant_type": "client_credentials",
#             "scope": "paymenttxn-v1fundTransfer paymentenq-paymentTransactionStatus cbs-acctenq-accountBalance cbs-acctenq-accountStatement",
#             "client_id": client_id,
#             "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
#             "client_assertion": token
#         }
        
#         # Add proxy support if needed
#         proxies = None
#         # If you need to use a proxy, uncomment and configure this:
#         # proxies = {
#         #     "http": "http://proxy.example.com:8080",
#         #     "https": "http://proxy.example.com:8080"
#         # }
        
#         # Print request details for debugging
#         logger.info(f"Making auth request to: {auth_url}")
#         logger.debug(f"Headers: Content-Type: application/x-www-form-urlencoded")
        
#         try:
#             # Gradually increase timeout if needed
#             auth_res = requests.post(
#                 auth_url, 
#                 data=authorized_payload,
#                 timeout=30,  # Increased timeout
#                 verify=True,  # Set to False only for testing
#                 proxies=proxies
#             )
            
#             logger.info(f"Auth response status code: {auth_res.status_code}")
            
#             if auth_res.status_code == 200:
#                 access_token = auth_res.json()['access_token']
#                 logger.info("Successfully obtained access token")
#                 return access_token
#             else:
#                 logger.error(f"Error fetching access token: {auth_res.status_code}")
#                 logger.error(f"Response text: {auth_res.text}")
#                 return None
                
#         except requests.exceptions.ConnectTimeout as e:
#             logger.error(f"Connection timeout: {str(e)}")
#             logger.error(f"Connection to {auth_url} timed out. Check network connectivity and firewall rules.")
#             return None
#         except requests.exceptions.SSLError as e:
#             logger.error(f"SSL Error: {str(e)}")
#             logger.error("This could be due to certificate validation issues. Check the server's CA certificates.")
#             return None
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Request exception: {str(e)}")
#             logger.error(traceback.format_exc())
#             return None
            
#     except Exception as e:
#         logger.error(f"Unexpected error in get_auth_tokens: {str(e)}")
#         logger.error(traceback.format_exc())
#         return None

# def transaction_process_imps(transaction):
#     try:
#         config = TransactionConfig.objects.first()
#         if not config:
#             logger.error("No TransactionConfig found in database")
#             return {"error": "Configuration not found"}
            
#         fund_transfer_url = config.fund_transfer_url
        
#         # Test connectivity first
#         if not diagnose_connection(fund_transfer_url):
#             logger.error(f"Cannot establish connection to {fund_transfer_url}")
#             return {"error": f"Cannot connect to API endpoint: {fund_transfer_url}"}
            
#         t_payload = {
#             "initiateAuthGenericFundTransferAPIReq": {
#                 "tellerBranch": "",
#                 "tellerID": "",
#                 "transactionID": transaction.transaction_id,
#                 "debitAccountNumber": transaction.debit_account_number,
#                 "creditAccountNumber": transaction.beneficiary.account_number,
#                 "remitterName": transaction.remitter_name,
#                 "amount": str(transaction.amount),
#                 "currency": "INR",
#                 "transactionType": "IMPS",
#                 "paymentDescription": transaction.payment_description,
#                 "beneficiaryIFSC": transaction.beneficiary.ifsc_code,
#                 "beneficiaryName": transaction.beneficiary.name,
#                 "beneficiaryAddress": "",
#                 "emailId": "abc@gmail.com",
#                 "mobileNo": "9999999999"
#             }
#         }

#         data = json.dumps(t_payload)  
#         secret_hex_key = config.secret_hex_key

#         encrypted = DynamicIVJce.encrypt(data, secret_hex_key)  
#         if not encrypted:
#             logger.error("Encryption failed")
#             return {"error": "Encryption failed."}
            
#         logger.info("Payload encrypted successfully")
            
#         access_token = get_auth_tokens()
#         if not access_token:
#             logger.error("Failed to get access token")
#             return {"error": "Failed to get access token."}
            
#         logger.info("Access token obtained successfully")
        
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/octet-stream",
#             "source": config.source,
#             "correlationId": "523134453sadaazd"
#         }
        
#         encrypted_payload = encrypted

#         logger.info(f"Making fund transfer request to: {fund_transfer_url}")
        
#         try:
#             # Increase timeout if network is slow
#             fund_t_response = requests.post(
#                 fund_transfer_url, 
#                 headers=headers, 
#                 data=encrypted_payload.encode("utf-8"),
#                 timeout=30,  # Increased timeout
#                 verify=True  # Set to False only for testing
#             )
            
#             logger.info(f"Fund transfer response status code: {fund_t_response.status_code}")
            
#             encrypted_payload = fund_t_response.text
#             decrypted = DynamicIVJce.decrypt(encrypted_payload, secret_hex_key)
            
#             if not decrypted:
#                 logger.error("Decryption failed")
#                 return {"error": "Decryption failed."}
                
#             logger.info("Response decrypted successfully")

#             result = json.loads(decrypted)
            
#             # Update transaction record
#             transaction.response_data = result
#             transaction.http_status_code = fund_t_response.status_code
#             transaction.txn_updated_timestamp = timezone.now()
#             transaction.txn_received_timestamp = result['initiateAuthGenericFundTransferAPIResp']['metaData']['time']
#             transaction.payment_description = result['initiateAuthGenericFundTransferAPIResp']['metaData']['message']
            
#             if result['initiateAuthGenericFundTransferAPIResp']['metaData']['status'] == "ERROR":
#                 transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['metaData']['status']
#             else:
#                 transaction.txn_status = result['initiateAuthGenericFundTransferAPIResp']['resourceData']['status']
#                 transaction.transaction_reference_no = result['initiateAuthGenericFundTransferAPIResp']['resourceData']['transactionReferenceNo']
                
#             transaction.save()
#             logger.info(f"Transaction record updated successfully with status: {transaction.txn_status}")
            
#             return result
            
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Request exception during fund transfer: {str(e)}")
#             return {"error": f"Fund transfer request failed: {str(e)}"}
            
#     except Exception as e:
#         logger.error(f"Unexpected error in transaction_process_imps: {str(e)}")
#         logger.error(traceback.format_exc())
#         return {"error": f"Unexpected error: {str(e)}"}

# # The other functions (get_transaction_status and fetch_bank_balance) would be 
# # similarly updated with error handling and diagnostics