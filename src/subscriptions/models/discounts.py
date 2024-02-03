from django.forms import ValidationError
from django.db import models
from subscriptions.models.invoice import Invoice
from core.utils.models import TimeStampedModel
from users.models import UserBase
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from subscriptions.utils import delete_unique_cards, generate_unique_cards


class Discount(TimeStampedModel):
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   related_name='discounts_created')
    last_updated_by = models.ForeignKey(UserBase,
                                        on_delete=models.SET_NULL,
                                        null=True,
                                        blank=True,
                                        related_name='discounts_updated')
    description = models.TextField(default='')
    code_prefix = models.CharField(max_length=255, unique=True)
    DISCOUNT_TYPES = (('percent', "Percent"), ('fixed', "Fixed"))
    discount_type = models.CharField(max_length=8,
                                     choices=DISCOUNT_TYPES,
                                     default='fixed')
    value = models.DecimalField(default=0.00, max_digits=60, decimal_places=2)

    is_limited = models.BooleanField(default=False)

    count_used = models.PositiveIntegerField(default=0)
    count_limit = models.PositiveIntegerField(default=1)
    has_unique_codes = models.BooleanField(default=False)

    is_available = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.code_prefix}'

    @property
    def discount_availability(self):
        if self.is_limited:
            return bool(self.count_limit - self.count_used) and self.is_active
        return self.is_active


@receiver(pre_save, sender=Discount)
def pre_save_handler_gift_card(sender, instance, *args, **kwargs):
    instance.is_available = instance.discount_availability
    if instance.has_unique_codes:
        if not instance.is_limited:
            raise ValidationError('To have discount with unique codes, '
                                  'is_limited must be set to True.')
    if instance.id:
        old_card = Discount.objects.get(id=instance.id)
        if old_card.has_unique_codes != instance.has_unique_codes:
            if old_card.count_used > 0:
                raise Exception(
                    'Cannot Edit Gift card if it is already has been used.')
            if instance.has_unique_codes:
                generate_unique_cards(instance, instance.count_limit)
        else:
            if instance.has_unique_codes:
                if old_card.count_limit != instance.count_limit:
                    if old_card.count_limit < instance.count_limit:
                        generate_unique_cards(
                            instance,
                            (instance.count_limit - old_card.count_limit))
                    if old_card.count_limit > instance.count_limit:
                        delete_unique_cards(
                            instance,
                            (old_card.count_limit - instance.count_limit))


class Code(TimeStampedModel):
    discount = models.ForeignKey(Discount,
                                 on_delete=models.CASCADE,
                                 related_name='codes')
    code = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.code}'


@receiver(post_save, sender=Discount)
def post_save_handler_gift_card(sender, instance, created, **kwargs):
    if created:
        generate_unique_cards(instance, instance.count_limit)


class DiscountRedeem(TimeStampedModel):
    redeemed_by = models.ForeignKey(UserBase, on_delete=models.PROTECT)
    code = models.ForeignKey(Code, on_delete=models.PROTECT)
    invoice = models.OneToOneField(Invoice,
                                   on_delete=models.PROTECT,
                                   related_name='redeemed_discount')
    discounted_amount = models.DecimalField(default=0.00,
                                            max_digits=60,
                                            decimal_places=2)


@receiver(pre_save, sender=DiscountRedeem)
def pre_save_redeem(sender, instance, *args, **kwargs):
    if not instance.id:
        if not instance.code.discount.is_available:
            raise ValidationError(
                'Sorry, this discount code is not available.')

        if instance.code.discount.is_limited:
            if instance.code.discount.has_unique_codes:
                instance.code.is_used = True
        instance.code.save()
        instance.code.discount.count_used += 1
        instance.code.discount.save()

    if instance.id:
        old = DiscountRedeem.objects.get(id=instance.id)
        if old.code != instance.code:
            raise ValidationError('Cannot update applied discount.')
        if old.invoice != instance.invoice:
            raise ValidationError('Cannot update attached invoice.')

    if instance.code.discount.discount_type == 'percent':
        instance.discounted_amount = (instance.invoice.subscription_charge *
                                      (instance.code.discount.value / 100))
    else:
        instance.discounted_amount = (instance.code.discount.value
                                      if instance.invoice.subscription_charge
                                      > instance.code.discount.value else 0)
    instance.invoice.save()
