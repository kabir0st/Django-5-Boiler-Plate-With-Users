from django.forms import ValidationError
from subscriptions.apis.filtersets import (CodeFilterSet, DiscountFilterSet,
                                           DiscountRedeemFilterSet)
from subscriptions.apis.serializers.discounts import (CodeSerializer,
                                                      DiscountRedeemSerializer,
                                                      DiscountSerializer,
                                                      MiniDiscountSerializer)
from subscriptions.models.discounts import Code, Discount, DiscountRedeem
from core.utils.permissions import IsAdmin
from core.utils.viewsets import DefaultViewSet
from rest_framework.decorators import action, permission_classes as ps
from rest_framework.permissions import AllowAny


class DiscountAPI(DefaultViewSet):
    serializer_class = DiscountSerializer
    queryset = Discount.objects.all().order_by('-id')
    search_fields = ['code_prefix', 'DISCOUNT_TYPES']
    permission_classes = [IsAdmin]
    filterset_class = DiscountFilterSet
    lookup_field = 'code_prefix'

    def get_serializer_class(self):
        if self.action == 'list':
            return MiniDiscountSerializer
        return super().get_serializer_class()

    @action(methods=['POST'], detail=False)
    @ps([AllowAny])
    def check_discount_code(self, request, *args, **kwargs):
        """
        Check if the discount code is valid or not. POST
        {
            "discount_code": __str__
        }
        """
        code = Code.objects.get(code=request.data['discount_code'])
        if code.is_used:
            raise ValidationError('Given discount code is already used.')
        return CodeSerializer(code).data


class CodeAPI(DefaultViewSet):
    serializer_class = CodeSerializer
    queryset = Code.objects.all().order_by('-id')
    search_fields = ['code']
    permission_classes = [IsAdmin]
    filterset_class = CodeFilterSet

    def get_queryset(self):
        if discount_pk := self.kwargs.get('discount_pk', None):
            return self.queryset.filter(discount__pk=discount_pk)
        return self.queryset.none()


class DiscountRedeemAPI(DefaultViewSet):
    serializer_class = DiscountRedeemSerializer
    queryset = DiscountRedeem.objects.all().order_by('-id')
    permission_classes = [IsAdmin]
    filterset_class = DiscountRedeemFilterSet

    def get_queryset(self):
        if discount_pk := self.kwargs.get('discount_pk', None):
            return self.queryset.filter(code__discount__pk=discount_pk)
        return self.queryset.none()
