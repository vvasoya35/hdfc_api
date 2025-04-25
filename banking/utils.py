from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
import base64
import json
import binascii
import random
import jwt
import datetime
from datetime import datetime, timedelta
import pytz
import time
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import requests
import uuid
import os


def generate_unique_jti() -> str:
    """
    Generate a unique JWT ID (jti) using UUID4.
    Returns:
        str: A unique jti string.
    """
    return str(uuid.uuid4())


def get_future_unix_time_ist(minutes_ahead=60):
    # Define IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    
    # Get current time in IST
    now_ist = datetime.now(ist)
    
    # Add specified minutes (default 60)
    future_time_ist = now_ist + timedelta(minutes=minutes_ahead)
    
    # Convert to UNIX timestamp
    unix_time = int(future_time_ist.timestamp())
    
    return unix_time


class DynamicIVJce:
    @staticmethod
    def generate_dynamic_iv():
        return ''.join(chr(random.randint(47, 126)) for _ in range(16)).encode('utf-8')

    @staticmethod
    def encrypt(data_to_encrypt, secret_hex_key):
        try:
            # Convert hex key to bytes
            key = binascii.unhexlify(secret_hex_key)
            if len(key) not in [16, 24, 32]:
                raise ValueError("Key length must be 16, 24, or 32 bytes")

            # Generate dynamic IV
            iv = DynamicIVJce.generate_dynamic_iv()

            # Initialize cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(data_to_encrypt.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_data)

            # Prefix IV and encode final payload
            final_output = iv + encrypted
            return base64.b64encode(final_output).decode('utf-8')
        except Exception as e:
            print("Encryption Error:", str(e))
            return None

    @staticmethod
    def decrypt(encrypted_base64, secret_hex_key):
        try:
            # Convert hex key to bytes
            key = binascii.unhexlify(secret_hex_key)
            if len(key) not in [16, 24, 32]:
                raise ValueError("Key length must be 16, 24, or 32 bytes")

            # Decode base64 to get IV + encrypted data
            combined_data = base64.b64decode(encrypted_base64)

            # Extract IV and encrypted payload
            iv = combined_data[:16]
            encrypted_data = combined_data[16:]

            # Initialize cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

            return decrypted.decode('utf-8')
        except Exception as e:
            print("Decryption Error:", str(e))
            return None
        
with open("private.key", "r") as key_file:
    private_key = key_file.read()
# Secret key (keep this safe!)

header = {
  "alg": "RS256",
  "typ": "JWT",
  "kid": "27e90681-12dc-4121-b385-06338831cd49"
}

# JWT payload (you can add more custom fields)
payload = {
"jti":generate_unique_jti(),
"sub":"5bc9f9ba-5ff2-4157-89df-3688a59bc29a",
"iss":"5bc9f9ba-5ff2-4157-89df-3688a59bc29a",
"aud":"https://app.uat-opt.idfcfirstbank.com/platform/oauth/oauth2/token", 
"exp":get_future_unix_time_ist()
}

# Encode the JWT
token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)


# print("Generated JWT:")
# print(token)
