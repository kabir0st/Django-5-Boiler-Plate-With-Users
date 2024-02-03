import uuid

from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now
from core.utils.models import TimeStampedModel
from subscriptions.models.subscription import Subscription
from users.models import UserBase


def generate_invoice_number():
    timestamp_part = timezone.now().strftime('%Y%m%d%H%M')
    random_part = str(uuid.uuid4().int)[:4]
    return f'LT-IV-{timestamp_part}-{random_part}'


class Invoice(TimeStampedModel):
    invoice_number = models.CharField(max_length=50, unique=True, default='')
    invoiced_on = models.DateTimeField(default=now)

    user = models.ForeignKey(UserBase,
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True,
                             related_name='invoices')
    subscription = models.ForeignKey(Subscription,
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     related_name='invoices')

    paid_for_in_days = models.PositiveIntegerField(default=30)
    amount_paid = models.PositiveIntegerField(default=0)
    amount_due = models.PositiveIntegerField(default=0)
    customer_email = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=255, default='draft')

    def __str__(self):
        return f"{self.invoice_number}"

    def is_paid(self):
        return self.status == 'paid'


@receiver(models.signals.pre_save, sender=Invoice)
def handle_invoice_summary_pre_save(sender, instance, *args, **kwargs):
    if not instance.invoice_number:
        while True:
            number = generate_invoice_number()
            if not Invoice.objects.filter(invoice_number=number).exists():
                instance.invoice_number = number
                break
