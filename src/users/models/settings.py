from core.utils.models import SingletonModel
from django.db import models


class GeneralSettings(SingletonModel):
    price_for_month = models.PositiveBigIntegerField(default=1000)
    price_for_trimonthly = models.PositiveBigIntegerField(default=2500)
