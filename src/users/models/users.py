from uuid import uuid4

from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.cache import cache
from django.db import models

from core.utils.models import TimeStampedModel


def default_array():
    return []


class UserbaseManager(BaseUserManager):

    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_agent", False)

        other_fields.setdefault("is_active", True)

        return self.create_user(email, password, **other_fields)

    def create_agent(self, email, password, **other_fields):
        other_fields.setdefault("is_staff", False)
        other_fields.setdefault("is_superuser", False)
        # Agent
        other_fields.setdefault("is_agent", True)
        other_fields.setdefault("is_active", True)
        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        other_fields.setdefault("is_superuser", False)
        other_fields.setdefault("is_staff", False)
        other_fields.setdefault("is_agent", False)

        if not email:
            raise ValueError("You must provide an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_provider_user(self, email, provider_uuid, **other_fields):
        other_fields.setdefault("is_superuser", False)
        other_fields.setdefault("is_staff", False)
        other_fields.setdefault("is_agent", False)
        other_fields.setdefault("is_superuser", False)
        if not email:
            raise ValueError("You must provide an email address")
        email = self.normalize_email(email)
        user = self.model(email=email,
                          provider_uuid=provider_uuid,
                          **other_fields)
        user.save()
        return user


def image_directory_path(instance, filename):
    return f"users/{instance.email}/{filename}"


class UserBase(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)

    provider = models.CharField(max_length=255,
                                default='',
                                null=True,
                                blank=True)
    provider_uuid = models.CharField(max_length=255,
                                     default='',
                                     null=True,
                                     blank=True)

    email = models.EmailField(unique=True)
    family_name = models.CharField(max_length=150, blank=True)
    given_name = models.CharField(max_length=150)

    phone_number = models.CharField(max_length=15, default='', blank=True)

    profile_image = models.ImageField(upload_to=image_directory_path,
                                      null=True,
                                      blank=True)

    is_verified = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    designation = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = "email"

    objects = UserbaseManager()

    def __str__(self):
        return f"{self.email}"

    class Meta:
        ordering = ["-id"]

    @property
    def is_subscribed(self):
        if hasattr(self, 'subscription') and self.subscription:
            return self.subscription.is_active
        return False

    @property
    def subscription_status(self):
        if hasattr(self, 'subscription') and self.subscription:
            return self.subscription.status
        return None

    @property
    def subscription_type(self):
        if hasattr(self, 'subscription') and self.subscription:
            return self.subscription.plan_str
        return None

    def update_cache(self, access_token):
        remaining_time = cache.ttl(access_token)
        cache.set(access_token, self, remaining_time)
        refresh = cache.get(f'refresh_{access_token}')
        remaining_time = cache.ttl(f'refresh_{access_token}')
        cache.set(refresh, self, remaining_time)
