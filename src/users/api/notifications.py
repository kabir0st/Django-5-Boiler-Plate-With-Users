from django.db.models import Q
from django_filters import FilterSet
from rest_framework.permissions import IsAuthenticated

from core.utils.viewsets import DefaultViewSet
from users.api.serializers.userbase import GlobalNotificationSerializer
from users.models import GlobalNotification


class GlobalNotificationFilters(FilterSet):

    class Meta:
        model = GlobalNotification
        fields = '__all__'


class NotificationAPI(DefaultViewSet):
    queryset = GlobalNotification.objects.all()
    serializer_class = GlobalNotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    search_fields = ['title']
    filterset_class = GlobalNotificationFilters

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_staff:
            return queryset
        if user.is_agent:
            return queryset.filter(
                Q(trigger_type='agents') | Q(trigger_type='all'))
        if user.is_subscribed:
            return queryset.filter(
                Q(trigger_type='subscribed') | Q(trigger_type='all'))
        return super().get_queryset().none()
