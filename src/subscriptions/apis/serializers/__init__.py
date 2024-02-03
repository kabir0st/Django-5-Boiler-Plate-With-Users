from rest_framework import serializers

from subscriptions.apis.serializers.discounts import DiscountRedeemSerializer
from subscriptions.models import FonePayPayment, Payment
from subscriptions.models.invoice import Invoice
from core.utils.functions import get_properties
from subscriptions.models.subscription import Subscription
from users.api.serializers.userbase import MiniUserBaseSerializer


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = '__all__'


class MiniInvoiceSerializer(serializers.ModelSerializer):
    invoiced_by_details = MiniUserBaseSerializer(source='invoiced_by',
                                                 read_only=True)
    properties = serializers.SerializerMethodField(read_only=True)

    def get_properties(self, obj):
        return get_properties(Invoice, obj)

    class Meta:
        model = Invoice
        exclude = ('id', )


class InvoiceSerializer(MiniInvoiceSerializer):
    subscription_serializer = SubscriptionSerializer(source='subscription',
                                                     many=True,
                                                     read_only=True)
    invoiced_by_details = MiniUserBaseSerializer(source='invoiced_by',
                                                 read_only=True)
    payments = serializers.SerializerMethodField(read_only=True)
    discount_code_used = DiscountRedeemSerializer(source='redeemed_discount',
                                                  read_only=True)

    def get_created_at(self, obj):
        return f"{obj.created_at}"

    def get_payments(self, obj):
        return ''

    class Meta:
        model = Invoice
        exclude = ('id', )


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'


class FonePayPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = FonePayPayment
        fields = '__all__'
