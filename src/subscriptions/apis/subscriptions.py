from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from core.utils.viewsets import DefaultViewSet
from subscriptions.apis.serializers import (InvoiceSerializer,
                                            SubscriptionSerializer)
from subscriptions.models.discounts import Code, DiscountRedeem
from subscriptions.models.invoice import Invoice
from subscriptions.models.subscription import Subscription
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


class SubscriptionAPI(DefaultViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.filter().order_by('-id')
    permission_classes = [IsAuthenticated]
    lookup_field = 'subscription_id'
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        if not hasattr(request.user, 'subscription'):
            return Response(
                {'msg': 'User has not bought any subscriptions yet.'},
                status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(request.user.subscription).data)

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    @action(methods=['post'], detail=False)
    def subscribe(self, request, *args, **kwargs):
        """
        Discount code can be used as referral code as well.
        SubscriptionType = month
        {
            'discount_code': <CODE>,
            'subscription_type': <SubscriptionType>
        }
        """
        data = request.data.copy()
        subs = Subscription.objects.filter(user=request.user).first()
        if subs and subs.status == "active":
            raise APIException(
                'User is already subscribed to an active subscription.')
        subscription_type = data.get('subscription_type', None)
        discount = data.get('discount_code', None)
        if discount:
            if code := Code.objects.filter(code=discount).first():
                if code.is_used:
                    raise APIException('Given discount code is already used.')
            else:
                raise APIException('Given discount code is Invalid.')
        if not subscription_type:
            return Response({'msg': 'Subscription type is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        price = 200
        with transaction.atomic():
            subs = Subscription.objects.create(
                user=request.user,
                status='inactive',
            )
            invoice = Invoice.objects.create(
                invoiced_by=request.user,
                subscription=subs,
                subscription_charge=price,
            )
            if discount:
                DiscountRedeem.objects.create(redeemed_by=request.user,
                                              code=code,
                                              invoice=invoice)
        return Response(
            {
                'msg': 'Subscription created.',
                'invoice': InvoiceSerializer(invoice).data
            },
            status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=True)
    def unsubscribe(self, request, *args, **kwargs):
        subscription = self.get_object()
        subscription.delete()
        return Response({
            'msg': 'User\'s subscription has been cancelled.',
        },
                        status=status.HTTP_200_OK)


def template_payment(request):
    return render(request, 'payment.html')
