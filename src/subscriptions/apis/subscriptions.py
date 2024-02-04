from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from core.utils.viewsets import DefaultViewSet
from subscriptions.apis.serializers import SubscriptionSerializer
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
        subs = Subscription.objects.filter(user=request.user).first()
        if subs and subs.status == "active":
            raise APIException(
                'User is already subscribed to an active subscription.')
        subscription_type = request.data.get('subscription_type', None)
        _ = request.data.get('discount_code', None)

        if not subscription_type:
            return Response({'msg': 'Subscription type is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            pass
        if subs:
            return Response(
                {
                    'msg': ('Your existing subscription has been '
                            'reassigned to you.'),
                    'subscription':
                    self.serializer_class(subs).data
                },
                status=status.HTTP_201_CREATED)
        return Response({'msg': 'Error creating subscription.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=True)
    def unsubscribe(self, request, *args, **kwargs):
        subscription = self.get_object()
        res, msg = (subscription)
        if not res:
            return Response({'msg': msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'msg': 'User\'s subscription has been cancelled.',
        },
                        status=status.HTTP_200_OK)


def template_payment(request):
    return render(request, 'payment.html')
