import uuid
from decimal import Decimal

from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from core.utils.models import TimeStampedModel
from users.models.userbase import UserBase

from .subscription import Subscription


def generate_invoice_number():
    timestamp_part = timezone.now().strftime('%Y%m%d%H%M')
    random_part = str(uuid.uuid4().int)[:4]
    return f'TLT-IV-{timestamp_part}-{random_part}'


class Invoice(TimeStampedModel):
    invoice_number = models.CharField(max_length=50,
                                      unique=True,
                                      default='',
                                      blank=True,
                                      null=True)
    invoiced_by = models.ForeignKey(UserBase,
                                    on_delete=models.SET_NULL,
                                    related_name='invoices',
                                    null=True,
                                    blank=True)

    subscription = models.ForeignKey(Subscription,
                                     related_name='invoice',
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     blank=True)
    subscription_charge = models.DecimalField(max_digits=10,
                                              decimal_places=2,
                                              default=0.00)

    staff_discount_amount = models.DecimalField(max_digits=10,
                                                decimal_places=2,
                                                default=0.00)
    staff_discount_remarks = models.CharField(max_length=255,
                                              blank=True,
                                              default='')

    total_discount_amount = models.DecimalField(max_digits=10,
                                                decimal_places=2,
                                                default=0.00)

    bill_amount = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0.00)
    paid_amount = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0.00)

    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.invoice_number}"

    @property
    def discount_from_discount_code(self):
        if hasattr(self, 'redeemed_discount'):
            return Decimal(self.redeemed_discount.discounted_amount)
        return Decimal('0.00')

    def check_is_paid(self):
        return self.paid_amount >= self.bill_amount

    def save_without_signals(self):
        models.signals.pre_save.disconnect(handle_invoice_summary_pre_save,
                                           sender=Invoice)
        models.signals.post_save.disconnect(handle_invoice_summary_post_save,
                                            sender=Invoice)
        self.save()
        models.signals.pre_save.connect(handle_invoice_summary_pre_save,
                                        sender=Invoice)
        models.signals.post_save.connect(handle_invoice_summary_post_save,
                                         sender=Invoice)


@receiver(models.signals.pre_save, sender=Invoice)
def handle_invoice_summary_pre_save(sender, instance, *args, **kwargs):
    if not instance.invoice_number:
        while True:
            number = generate_invoice_number()
            if not Invoice.objects.filter(invoice_number=number).exists():
                instance.invoice_number = number
                break
    instance.paid_amount = Decimal('0.00')

    fields_to_convert = [
        'bill_amount', 'staff_discount_amount', 'total_discount_amount',
        'subscription_charge'
    ]
    for field in fields_to_convert:
        setattr(instance, field, Decimal(str(getattr(instance, field))))


@receiver(models.signals.post_save, sender=Invoice)
def handle_invoice_summary_post_save(sender, instance, *args, **kwargs):
    instance.total_discount_amount = (instance.staff_discount_amount +
                                      instance.discount_from_discount_code)
    instance.bill_amount = (instance.subscription_charge -
                            instance.total_discount_amount)
    instance.paid_amount = sum(
        payment.amount
        for payment in instance.payments.filter(is_refunded=False))
    instance.is_paid = instance.check_is_paid()
    instance.save_without_signals()
