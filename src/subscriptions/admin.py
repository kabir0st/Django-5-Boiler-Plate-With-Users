from django.contrib import admin
from unfold.admin import ModelAdmin
from subscriptions.models.discounts import Code, Discount, DiscountRedeem

from subscriptions.models.invoice import Invoice, Subscription
from subscriptions.models.payments import FonePayPayment, Payment


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('invoice_number', 'bill_amount', 'paid_amount',
                    'subscription_charge')
    search_fields = ['invoice_number', 'user__username', 'customer_email']
    list_filter = ['is_paid', 'created_at']
    readonly_fields = ('is_paid', )


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = (
        'subscription_id',
        'user',
        'status',
        'current_starts',
        'current_period_end',
        'start_date',
    )
    search_fields = ['subscription_id', 'user__username']
    list_filter = [
        'status',
    ]
    readonly_fields = ('status', )


@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = (
        'code_prefix',
        'discount_type',
        'value',
        'count_used',
        'count_limit',
        'has_unique_codes',
    )
    search_fields = ('code_prefix', )
    list_filter = ('discount_type', 'has_unique_codes', 'is_limited')
    readonly_fields = ('count_used', )


@admin.register(Code)
class CodeAdmin(ModelAdmin):
    list_display = ('discount', 'code', 'is_used')
    search_fields = ('code', )
    list_filter = ('is_used', )
    readonly_fields = ('code', )


@admin.register(DiscountRedeem)
class DiscountRedeemAdmin(ModelAdmin):
    list_display = ('redeemed_by', 'code', 'discounted_amount', 'invoice')
    search_fields = ('redeemed_by__email', 'discount__name', 'code__code')

    def code(self, obj):
        return obj.code.code


class FonePayPaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'amount', 'qr_status',
                    'is_verified_from_server', 'trace_id', 'ird_details_sent')
    list_filter = ('qr_status', 'is_verified_from_server', 'ird_details_sent')
    search_fields = ('invoice_number', 'amount', 'qr_status')
    readonly_fields = ('last_response_from_fonepay', )


admin.site.register(FonePayPayment, FonePayPaymentAdmin)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'amount', 'invoice_summary', 'is_refunded')
    list_filter = ('payment_type', 'is_refunded')
    search_fields = ('payment_type', 'amount',
                     'invoice_summary__invoice_number')
    readonly_fields = ('invoice_summary', )


admin.site.register(Payment, PaymentAdmin)
