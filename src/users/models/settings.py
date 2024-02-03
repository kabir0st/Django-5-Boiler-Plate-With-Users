from core.utils.models import SingletonModel
from django.db import models


class Settings(SingletonModel):
    price_for_30_days = models.PositiveBigIntegerField(default=1000)
