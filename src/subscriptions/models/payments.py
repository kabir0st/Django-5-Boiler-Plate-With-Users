from django.dispatch import receiver
from core.utils.models import TimeStampedModel
from django.db import models

from users.models.userbase import UserBase

from .invoice import Invoice


class FonePayPayment(TimeStampedModel):
    STATUS_CHOICE = (
        ('initiated', 'initiated'),
        ('requested', 'requested'),
        ('failed', 'failed'),
        ('success', 'success'),
    )
    qr_status = models.CharField(max_length=255,
                                 choices=STATUS_CHOICE,
                                 default='initiated')
    amount = models.DecimalField(default=0.00, max_digits=60, decimal_places=2)
    last_response_from_fonepay = models.TextField(null=True, blank=True)
    invoice_number = models.CharField(max_length=255)
    is_verified_from_server = models.BooleanField(default=False)
    trace_id = models.TextField(default='', blank=True, null=True)
    ird_details_sent = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.invoice_number} {self.amount} {self.qr_status}'

    def save(self, *args, **kwargs):
        if self.ird_details_sent:
            raise Exception(
                'Cannot update payment record that is already '
                'verified and IRD details has been sent to FonePay.')
        return super().save(*args, **kwargs)


class Payment(TimeStampedModel):
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   related_name='payments')
    PAYMENT_TYPE_CHOICES = (('fonepay', 'Fonepay'),
                            ('staff_approved', 'Staff Approved'), ('stripe',
                                                                   'Stripe'))
    payment_type = models.CharField(max_length=15,
                                    choices=PAYMENT_TYPE_CHOICES,
                                    default='fonepay')

    fonepay_payment = models.ForeignKey(FonePayPayment,
                                        on_delete=models.PROTECT,
                                        null=True,
                                        blank=True)
    amount = models.DecimalField(default=0.00, max_digits=60, decimal_places=2)

    invoice = models.ForeignKey(Invoice,
                                on_delete=models.PROTECT,
                                related_name='payments')
    remarks = models.TextField(default='', blank=True)

    is_refunded = models.BooleanField(default=False)
    refunded_remarks = models.TextField(default='', blank=True)

    def __str__(self):
        return f'{self.payment_type} {self.amount}'


@receiver(models.signals.post_save, sender=Payment)
def handle_payment_post_save(sender, instance, *args, **kwargs):
    instance.invoice.save()
