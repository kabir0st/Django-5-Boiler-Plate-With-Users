from builtins import AttributeError

from django.db.models import FileField, ImageField, TextField, JSONField
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action

from core.utils.functions import export_data

EXCLUDE = [ImageField, FileField, TextField, JSONField]
EXCLUDE_FIELD_NAMES = ['password', 'is_superuser']


class DefaultViewSet(ModelViewSet):

    @property
    def ordering_fields(self):
        try:
            queryset = self.queryset or self.get_queryset()
            return [
                field.name for field in queryset.model._meta.fields if not any(
                    isinstance(field, e)
                    for e in EXCLUDE) and field.name not in EXCLUDE_FIELD_NAMES
            ]
        except AttributeError:
            return []

    @property
    def filterset_fields(self):
        try:
            queryset = self.queryset or self.get_queryset()
            return [
                field.name for field in queryset.model._meta.fields if not any(
                    isinstance(field, e)
                    for e in EXCLUDE) and field.name not in EXCLUDE_FIELD_NAMES
            ]
        except AttributeError:
            return []

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if _ := request.GET.get('hardDelete', None):
            with transaction.atomic():
                instance.delete()
            msg = 'Deleted successfully.'
        else:
            msg = 'Disabled successfully.'
            instance.is_active = False
            instance.save()
        return Response({'status': True, 'msg': msg})

    @action(methods=['GET'], detail=False)
    def export(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        document_name = request.GET.get('document_name',
                                        queryset.model.__name__)
        if document_name:
            document_name = str(document_name).title()
        model = f'{queryset.model._meta.app_label}.{queryset.model.__name__}'

        response = {
            'status':
            True,
            'document':
            export_data(model, [item.id for item in queryset], document_name)
        }
        return Response(response)


class SingletonViewSet(ModelViewSet):

    def destroy(self, request, *args, **kwargs):
        return Response({'status': False, 'msg': 'Cannot remove settings.'})

    def retrieve_instance(self):
        instance = self.get_queryset().first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request):
        return self.retrieve_instance()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_instance()

    def create(self, request, *args, **kwargs):
        obj = self.get_queryset().first()
        if obj is None:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            serializer = self.get_serializer(instance=obj, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)
