import jwt
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os
import uuid
import datetime
import pytz

# Helper functions

def generate_unique_jti():
    return str(uuid.uuid4())

def get_future_unix_time_ist(minutes=15):
    ist = pytz.timezone('Asia/Kolkata')
    exp_time = datetime.datetime.now(ist) + datetime.timedelta(minutes=minutes)
    return int(exp_time.timestamp())

class DynamicIVJce:
    @staticmethod
    def encrypt(plain_text, hex_key):
        key = bytes.fromhex(hex_key)
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
        return base64.b64encode(iv + encrypted).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_text, hex_key):
        key = bytes.fromhex(hex_key)
        encrypted_data = base64.b64decode(encrypted_text)
        iv = encrypted_data[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size)
        return decrypted.decode('utf-8')
