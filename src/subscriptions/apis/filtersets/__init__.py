import django_filters
from django_filters import FilterSet

from subscriptions.models import Invoice, Code, DiscountRedeem, Discount


class InvoiceFilterSet(django_filters.FilterSet):
    paid_amount__range = django_filters.RangeFilter()
    subscription_charge__range = django_filters.RangeFilter()
    staff_discount_amount__range = django_filters.RangeFilter()
    total_discount_amount__range = django_filters.RangeFilter()
    bill_amount__range = django_filters.RangeFilter()

    class Meta:
        model = Invoice
        fields = '__all__'


class DiscountFilterSet(django_filters.FilterSet):
    value__range = django_filters.RangeFilter()
    count_used__range = django_filters.RangeFilter()
    count_limit__range = django_filters.RangeFilter()

    class Meta:
        model = Discount
        fields = '__all__'


class CodeFilterSet(FilterSet):

    class Meta:
        model = Code
        fields = '__all__'


class DiscountRedeemFilterSet(FilterSet):

    class Meta:
        model = DiscountRedeem
        fields = '__all__'
