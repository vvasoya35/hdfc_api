from django.contrib import admin
from .models import FundTransferTransaction, Beneficiary, TransactionConfig, Users_ips
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from .services import fetch_bank_balance
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = 'Kachubuka Textile'  # This will change the site name at the top
    site_title = 'Kachubuka Textile Admin'  # This changes the title in the browser tab
    index_title = 'Welcome to Kachubuka Textile Admin'  # This changes the title on the main admin page

# Register the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')


class TransactionConfigAdmin(admin.ModelAdmin):
    change_list_template = "admin/transaction_config_change_list.html"  # custom template

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch-balance/', self.admin_site.admin_view(self.fetch_balance), name='fetch-balance'),
        ]
        return custom_urls + urls

    def fetch_balance(self, request):
        try:
            balance_data = fetch_bank_balance()
            return JsonResponse(balance_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

admin.site.register(TransactionConfig, TransactionConfigAdmin)

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