from django.urls import include, path
from rest_framework.routers import SimpleRouter
from subscriptions.apis.discounts import (CodeAPI, DiscountAPI,
                                          DiscountRedeemAPI)
from subscriptions.apis.invoices import InvoiceAPI

from subscriptions.apis.subscriptions import SubscriptionAPI
from rest_framework_nested.routers import NestedDefaultRouter

router = SimpleRouter()
router.register('discounts', DiscountAPI)

subs_router = NestedDefaultRouter(router, r'discounts', lookup='code_prefix')
subs_router.register('codes', CodeAPI)

router.register('discounts/redeemed', DiscountRedeemAPI)
router.register('invoices', InvoiceAPI)
router.register('', SubscriptionAPI)

urlpatterns = [
    path('', include(router.urls)),
]
