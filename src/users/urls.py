from django.urls import include, path
from rest_framework.routers import SimpleRouter
from users.api.notifications import NotificationAPI
from users.api.users import RegisterUserBaseAPI, UserBaseAPI
from users.api.auth import (forget_password, reset_password)

router = SimpleRouter()

router.register('base', UserBaseAPI, basename='Users')
router.register('notifications', NotificationAPI)

urlpatterns = [
    path('register/', RegisterUserBaseAPI.as_view()),
    path('password/reset/', reset_password),
    path('password/forget/', forget_password),
    path('', include(router.urls)),
]
