from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib.auth.models import Group

from users.models.supports import Notification

from .models import (Document, GeneralSettings, UserBase, VerificationCode,
                     GlobalNotification)


@admin.register(GeneralSettings)
class SettingsAdmin(ModelAdmin):
    pass


@admin.register(UserBase)
class UserAdmin(ModelAdmin):
    model = UserBase
    fieldsets = (
        (None, {
            'fields': ['email', 'referred_by']
        }),
        ('Personal Info', {
            'fields':
            ['family_name', 'given_name', 'phone_number', 'profile_image']
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_agent', 'is_verified',
                       'designation'),
            'classes': ('collapse', )
        }),
        ('Login Provider Info', {
            'fields': ('provider', 'provider_uuid'),
            'classes': ('collapse', )
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse', )
        }),
    )
    list_display = ('email', 'given_name', 'family_name', 'is_staff',
                    'is_agent', 'is_active')
    search_fields = ('email', 'given_name', 'family_name')
    readonly_fields = ('created_at', 'updated_at', 'password')
    ordering = ('email', )


@admin.register(VerificationCode)
class VerificationCodeAdmin(ModelAdmin):
    list_display = ('email', 'code', 'is_email_sent')
    search_fields = ('email', 'code')
    list_filter = ('is_email_sent', )


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ('uuid', 'name', 'model', 'status')
    search_fields = ('uuid', 'name', 'model')
    list_filter = ('status', )


@admin.register(GlobalNotification)
class GlobalNotificationAdmin(ModelAdmin):
    pass


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    model = Notification
    autocomplete_fields = [
        'user',
    ]


admin.site.unregister(Group)
