import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        try:
            if data.startswith('data:image'):
                format_, imgstr = data.split(';base64,')
                ext = format_.split('/')[-1]
                name = uuid.uuid4()
                data = ContentFile(base64.b64decode(imgstr),
                                   name=f'{name}.{ext}')
        except Exception as exp:
            raise Exception(f'Invalid Base64 format. {exp}')
        return super().to_internal_value(data)


class Base64FileField(serializers.FileField):

    def to_internal_value(self, data):
        try:
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=f'{name}.{ext}')
        except Exception as exp:
            raise Exception(f'Invalid Base64 format. {exp}')
        return super().to_internal_value(data)
