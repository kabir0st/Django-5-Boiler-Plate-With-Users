from rest_framework import serializers

from users.models import (UserBase)
from users.models.notification import Notification
from users.models.supports import VerificationCode
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from core.utils.functions import get_properties


class LowercaseEmailValidator:

    def __call__(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower()


class RegisterUserBaseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[LowercaseEmailValidator()])

    class Meta:
        model = UserBase
        fields = ('email', 'password', 'family_name', 'given_name',
                  'profile_image')

        extra_kwargs = {
            'is_verified': {
                'read_only': True
            },
            'is_staff': {
                'read_only': True
            },
            'is_agent': {
                'read_only': True
            },
            'last_login': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        validated_data['is_agent'] = False
        validated_data['provider'] = 'email'
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        VerificationCode.generate(validated_data['email'],
                                  'email_verification')
        return instance


class UserBaseSerializer(serializers.ModelSerializer):
    properties = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserBase
        read_only_fields = ('is_active', 'is_staff', 'is_agent', 'is_verified',
                            'last_login', 'created_at', 'updated_at',
                            'is_subscribed')

        exclude = [
            'password', 'is_superuser', 'provider_uuid', 'groups',
            'user_permissions', 'last_login'
        ]

    def get_properties(self, obj):
        return get_properties(UserBase, obj)


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'
