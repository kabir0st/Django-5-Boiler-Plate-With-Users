from subscriptions.models import Discount, DiscountRedeem, Code

from rest_framework import serializers
from core.utils.functions import get_properties

from users.api.serializers.userbase import MiniUserBaseSerializer


class MiniDiscountSerializer(serializers.ModelSerializer):
    properties = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Discount
        fields = ('id', 'description', 'code_prefix', 'discount_type', 'value',
                  'is_limited', 'count_used', 'count_limit',
                  'has_unique_codes', 'is_available', 'properties')

    def get_properties(self, obj):
        return get_properties(Discount, obj)


class DiscountSerializer(MiniDiscountSerializer):
    created_by_details = MiniUserBaseSerializer(source='created_by',
                                                read_only=True)

    last_updated_by_details = MiniUserBaseSerializer(source='last_updated_by',
                                                     read_only=True)

    class Meta:
        model = Discount
        fields = '__all__'


class CodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Code
        fields = '__all__'


class DiscountRedeemSerializer(serializers.ModelSerializer):
    redeemed_by_details = MiniUserBaseSerializer(source='redeemed_by',
                                                 read_only=True)
    code_details = CodeSerializer(source='code', read_only=True)

    class Meta:
        model = DiscountRedeem
        fields = '__all__'
