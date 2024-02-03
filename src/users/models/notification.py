from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.tasks import send_notifications


class Notification(models.Model):
    ALL = 'all'
    SUBSCRIBED = 'subscribed'
    AGENTS = 'agents'

    NOTIFICATION_TYPE_CHOICES = [
        (ALL, 'All'),
        (SUBSCRIBED, 'Subscribed'),
        (AGENTS, 'Agents'),
    ]
    title = models.CharField(max_length=255)
    msg = models.TextField(default='')
    trigger_type = models.CharField(max_length=20,
                                    choices=NOTIFICATION_TYPE_CHOICES)

    is_processed = models.BooleanField(default=False)


@receiver(post_save, sender=Notification)
def post_save(sender, instance, *args, **kwargs):
    if not instance.is_processed:
        send_notifications.delay(instance.id)
