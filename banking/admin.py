from django.contrib import admin
from .models import FundTransferTransaction, Beneficiary, TransactionConfig, Users_ips
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from .services import fetch_bank_balance
from django.contrib.admin import AdminSite
from django.db.models import Sum, Count
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

class DateRangeFilter(SimpleListFilter):
    title = _('Transaction Date Range')  # Filter title
    parameter_name = 'date_range'  # URL parameter name for filtering

    def lookups(self, request, model_admin):
        return (
            ('last_7_days', _('Last 7 days')),
            ('last_30_days', _('Last 30 days')),
            ('custom', _('Custom range')),
        )

    def queryset(self, request, queryset):
        from datetime import timedelta
        from django.utils.timezone import now

        # Get the current date
        today = now().date()

        if self.value() == 'last_7_days':
            start_date = today - timedelta(days=7)
            return queryset.filter(created_at__date__gte=start_date)
        elif self.value() == 'last_30_days':
            start_date = today - timedelta(days=30)
            return queryset.filter(created_at__date__gte=start_date)
        elif self.value() == 'custom':
            # For custom range, let the admin select start and end dates in the admin panel
            return queryset
        return queryset


class CustomAdminSite(AdminSite):
    site_header = 'Kachubuka Textile'  # This will change the site name at the top
    site_title = 'Kachubuka Textile Admin'  # This changes the title in the browser tab
    index_title = 'Welcome to Kachubuka Textile Admin'  # This changes the title on the main admin page

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
    list_filter = ('transaction_type', 'txn_status', DateRangeFilter)
    search_fields = ('transaction_id', 'transaction_reference_no', 'beneficiary__name', 'debit_account_number')
    ordering = ('-created_at',)
    readonly_fields = ('unique_id', 'created_at', 'updated_at')

    def changelist_view(self, request, extra_context=None):
        # Get the filter date range
        date_range = request.GET.get('date_range', 'last_7_days')

        # Set up default date filter
        from datetime import timedelta
        from django.utils.timezone import localtime

        today = localtime(now()).date()
        if date_range == 'last_7_days':
            start_date = today - timedelta(days=7)
            queryset = FundTransferTransaction.objects.filter(created_at__date__gte=start_date)
        elif date_range == 'last_30_days':
            start_date = today - timedelta(days=30)
            queryset = FundTransferTransaction.objects.filter(created_at__date__gte=start_date)
        elif date_range == 'custom':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if start_date and end_date:
                queryset = FundTransferTransaction.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
            else:
                queryset = FundTransferTransaction.objects.none()  # No transactions if no custom date is selected
        else:
            queryset = FundTransferTransaction.objects.none()

        total_amount = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        total_count = queryset.aggregate(Count('id'))['id__count']

        extra_context = extra_context or {}
        extra_context['today_total_amount'] = total_amount
        extra_context['today_total_count'] = total_count
        extra_context['selected_date_range'] = date_range

        return super().changelist_view(request, extra_context=extra_context)


# class FundTransferTransactionAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'transaction_id',
#         'transaction_reference_no',
#         'beneficiary',
#         'amount',
#         'transaction_type',
#         'txn_status',
#         'created_at',
#         'updated_at',
#     )
#     list_filter = ('transaction_type', 'txn_status', 'created_at')
#     search_fields = ('transaction_id', 'transaction_reference_no', 'beneficiary__name', 'debit_account_number')
#     ordering = ('-created_at',)
#     readonly_fields = ('unique_id', 'created_at', 'updated_at')

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