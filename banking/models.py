from django.db import models
import uuid
import random

# Create your models here.
class Beneficiary(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=32)
    ifsc_code = models.CharField(max_length=11)
    address = models.TextField(blank=True, null=True)
    email_id = models.EmailField(default="abc@gmail.com")
    mobile_no = models.CharField(max_length=15, default="9999999999")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Unnamed'} ({self.account_number})"


class FundTransferTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("NEFT", "NEFT"),
        ("RTGS", "RTGS"),
        ("IMPS", "IMPS"),
        ("IFT", "IFT"),
    ]

    STATUS_CHOICES = [
        ("INITIATED", "Initiated"),
        ("ACPT", "Accepted"),
        ("REJECTED", "Rejected"),
        ("FAILED", "Failed"),
        ("ERROR", "Error"),
    ]

    beneficiary = models.ForeignKey("Beneficiary", on_delete=models.PROTECT)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    transaction_reference_no = models.CharField(max_length=50, blank=True, null=True)
    debit_account_number = models.CharField(max_length=20)
    remitter_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES,default="IMPS")
    payment_description = models.CharField(max_length=120, blank=True, null=True)
    message_type = models.CharField(max_length=10, blank=True, null=True)

    txn_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="INITIATED")
    txn_received_timestamp = models.DateTimeField(blank=True, null=True)
    txn_updated_timestamp = models.DateTimeField(blank=True, null=True)

    http_status_code = models.IntegerField(null=True, blank=True)
    response_data = models.TextField(null=True, blank=True)

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_reference_no}"
        # return f"{self.transaction_type} - {self.transaction_reference_no or self.transaction_id or 'N/A'}"
    
    def save(self, *args, **kwargs):
        # 👉 Rule: If transaction is RTGS, set message_type to "R41"
        if self.transaction_type == "RTGS":
            self.message_type = "R41"

        if not self.transaction_id:
            self.transaction_id = self.generate_unique_transaction_id()

        super().save(*args, **kwargs)

    def generate_unique_transaction_id(self):
        while True:
            random_id = ''.join([str(random.randint(0, 9)) for _ in range(11)])
            if not FundTransferTransaction.objects.filter(transaction_id=random_id).exists():
                return random_id


class Users_ips(models.Model):
    ip_address = models.GenericIPAddressField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address}"

class TransactionConfig(models.Model):
    compnay_name = models.CharField(max_length=100)
    debit_account_number = models.CharField(max_length=20)
    remitter_name = models.CharField(max_length=100)
    client_id = models.CharField(max_length=100)
    secret_hex_key = models.CharField(max_length=255)
    private_key = models.TextField()  # store your RSA private key
    kid = models.CharField(max_length=100)  # key id for JWT
    sub = models.CharField(max_length=100)
    iss = models.CharField(max_length=100)
    aud = models.URLField()
    auth_url = models.URLField(default='')
    fund_transfer_url = models.URLField(default='')
    transaction_status_url = models.URLField(default='')
    source = models.CharField(max_length=10)  # key cert algorithm
    get_balance_url = models.URLField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Transaction Config"
        
