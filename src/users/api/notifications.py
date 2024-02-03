from django.db.models import Q
from django_filters import FilterSet
from rest_framework.permissions import IsAuthenticated

from core.utils.viewsets import DefaultViewSet
from users.api.serializers.userbase import NotificationSerializer
from users.models.notification import Notification


class NotificationFilters(FilterSet):

    class Meta:
        model = Notification
        fields = '__all__'


class NotificationAPI(DefaultViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    search_fields = ['title']
    filterset_class = NotificationFilters

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
