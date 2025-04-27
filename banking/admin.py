from django.contrib import admin
from .models import FundTransferTransaction, Beneficiary, TransactionConfig, Users_ips

@admin.register(FundTransferTransaction)
class FundTransferTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'transaction_id',
        'transaction_reference_no',
        'beneficiary',
        'amount',
        'transaction_type',
        'txn_status',
        'created_at',
        'updated_at',
    )
    list_filter = ('transaction_type', 'txn_status', 'created_at')
    search_fields = ('transaction_id', 'transaction_reference_no', 'beneficiary__name', 'debit_account_number')
    ordering = ('-created_at',)
    readonly_fields = ('unique_id', 'created_at', 'updated_at')

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'account_number',
        'ifsc_code',
        'email_id',
        'mobile_no',
        'created_at',
    )
    search_fields = ('name', 'account_number', 'ifsc_code')
    ordering = ('-created_at',)

@admin.register(Users_ips)
class Users_ipsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ip_address',
        'notes',
        'created_at',
    )
    search_fields = ('ip_address', 'notes')
    ordering = ('-created_at',)

admin.site.register(TransactionConfig)