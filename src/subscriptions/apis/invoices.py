from decimal import Decimal

from django.db import transaction
from django.forms import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils.permissions import IsStaffOrReadOnly
from core.utils.viewsets import DefaultViewSet
from subscriptions.apis.filtersets import InvoiceFilterSet
from subscriptions.apis.serializers import (InvoiceSerializer,
                                            MiniInvoiceSerializer,
                                            PaymentSerializer)
from subscriptions.models import Invoice, Payment
from subscriptions.models.discounts import Code, DiscountRedeem
from subscriptions.models.payments import FonePayPayment
from subscriptions.utils import generate_fonepay_qr, verify_qr


class InvoiceAPI(DefaultViewSet):
    serializer_class = InvoiceSerializer
    search_fields = ["invoice_number", "bookings__booking_number"]
    queryset = Invoice.objects.filter().order_by('-id')
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filterset_class = InvoiceFilterSet
    lookup_field = "invoice_number"

    def get_serializer_class(self):
        if self.action == 'list':
            return MiniInvoiceSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(invoiced_by=self.request.user)

    @action(methods=['POST', 'GET'], detail=True)
    def apply_discount_code(self, request, *args, **kwargs):
        if request.method == 'GET':
            return Response({'status': True})
        instance = self.get_object()
        if instance.is_paid:
            raise ValidationError(
                'Cannot apply discount code to invoice that\'s '
                'already been paid.')
        if hasattr(instance, 'redeemed_discount'):
            raise ValidationError('Only one discount code can be applied.')
        code = Code.objects.get(code=request.data['code'])
        if code.is_used:
            raise ValidationError('Given discount code is already used.')
        DiscountRedeem.objects.create(redeemed_by=request.user,
                                      code=code,
                                      invoice=instance)
        return Response({
            'status': True,
            'msg': "Discount Applied"
        },
                        status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def staff_approved_payment(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise ValidationError(
                'Only Staff can add staff approved payments.')
        summary = self.get_object()
        with transaction.atomic():
            Payment.objects.create(created_by=request.user,
                                   payment_type='staff_approved',
                                   amount=Decimal(f'{request.data["amount"]}'),
                                   invoice=summary,
                                   remarks='Payment Through API')
        return Response(InvoiceSerializer(summary).data,
                        status=status.HTTP_202_ACCEPTED)

    @action(methods=['post'], detail=True)
    def initiate_fonepay(self, request, *args, **kwargs):
        obj = self.get_object()
        fonepay_obj = FonePayPayment.objects.create(
            amount=request.data['amount'], invoice_number=obj.invoice_number)
        res = generate_fonepay_qr(fonepay_obj)
        return Response(res)

    @action(methods=['post'], detail=True)
    def verify_fonepay(self, request, *args, **kwargs):
        obj = FonePayPayment.objects.get(id=request.data['fonepay_payment_id'])
        obj.qr_status = 'success'
        obj.save()
        if obj.is_verified_from_server:
            raise Exception('Cannot verify payments that is already verified')
        with transaction.atomic():
            res = verify_qr(obj)
            if res['status']:
                payment_data = {
                    'amount': obj.amount,
                    'fonepay_payment': obj.id,
                    'payment_type': 'fonepay',
                    'invoice': self.get_object().id
                }
                serializer = PaymentSerializer(data=payment_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({
                    'status': True,
                    'msg': 'Payment successful.',
                    'data-type': 'payment',
                    'data': serializer.data
                })
        return Response({
            'status': False,
            'msg': 'There was problem verifying your payment.',
            'exception': res['text']
        })
