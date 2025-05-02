from celery import shared_task
from django.utils import timezone
from .models import FundTransferTransaction
from .services import get_transaction_status

@shared_task
def check_pending_transactions():
    pending_txns = FundTransferTransaction.objects.exclude(txn_status__in=["SUCCESS", "ERROR"])
    for txn in pending_txns:
        new_status = get_transaction_status(txn) 
