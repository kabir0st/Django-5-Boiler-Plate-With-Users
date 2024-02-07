import uuid

from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now

from users.models import UserBase


def generate_invoice_number():
    timestamp_part = timezone.now().strftime('%Y%m%d%H%M')
    random_part = str(uuid.uuid4().int)[:4]
    return f'SUB-{timestamp_part}-{random_part}'


class Subscription(models.Model):

    subscription_id = models.CharField(max_length=255,
                                       unique=True,
                                       default='',
                                       blank=True)
    user = models.OneToOneField(UserBase,
                                on_delete=models.SET_NULL,
                                null=True,
                                related_name='subscription',
                                unique=True)

    # data we get from stripe
    # incomplete, incomplete_expired, trialing,
    # active, past_due, canceled, or unpaid
    status = models.CharField(max_length=255, default='deactivated')
    current_starts = models.PositiveBigIntegerField(default=0)
    current_period_end = models.PositiveBigIntegerField(default=0)
    start_date = models.PositiveBigIntegerField(default=0)

    @property
    def is_active(self):
        if self.current_period_end < now().timestamp():
            return False
        return self.status == 'active'


@receiver(models.signals.pre_save, sender=Subscription)
def handle_subscription_pre_save(sender, instance, *args, **kwargs):
    if not instance.subscription_id:
        while True:
            number = generate_invoice_number()
            if not Subscription.objects.filter(
                    subscription_id=number).exists():
                instance.subscription_id = number
                break
