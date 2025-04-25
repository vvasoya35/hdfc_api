from django.db import models
import uuid

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
    ]

    beneficiary = models.ForeignKey("Beneficiary", on_delete=models.PROTECT)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    transaction_reference_no = models.CharField(max_length=50, blank=True, null=True)
    debit_account_number = models.CharField(max_length=20)
    remitter_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
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
    retry_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_reference_no or self.transaction_id or 'N/A'}"
