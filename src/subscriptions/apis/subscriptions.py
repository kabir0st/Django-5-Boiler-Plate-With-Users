from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils.viewsets import DefaultViewSet
from subscriptions.apis.serializers import (InvoiceSerializer,
                                            SubscribeSerializer,
                                            SubscriptionSerializer)
from subscriptions.models.subscription import Subscription


class SubscriptionAPI(DefaultViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.filter().order_by('-id')
    permission_classes = [IsAuthenticated]
    lookup_field = 'subscription_id'
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribeSerializer
        return super().get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            return super().list(self, request, *args, **kwargs)
        if not hasattr(request.user, 'subscription'):
            return Response(
                {'msg': 'User has not bought any subscriptions yet.'},
                status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(request.user.subscription).data)

    @action(methods=['get', 'post'], detail=False)
    def subscribe(self, request, *args, **kwargs):
        """
        Discount code can be used as referral code as well.
        SubscriptionType = month
        {
            'discount_code': <CODE>,
            'subscription_type': <SubscriptionType>
        }
        """
        if request.method == 'GET':
            return Response('For testing.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(
            {
                'msg':
                'Subscription initiated. Please pay the invoice to activate'
                ' your subscription',
                'invoice':
                InvoiceSerializer(invoice).data
            },
            status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=True)
    def unsubscribe(self, request, *args, **kwargs):
        subscription = self.get_object()
        subscription.delete()
        return Response({
            'msg': 'Your subscription has been cancelled.',
        },
                        status=status.HTTP_200_OK)


def template_payment(request):
    return render(request, 'payment.html')
