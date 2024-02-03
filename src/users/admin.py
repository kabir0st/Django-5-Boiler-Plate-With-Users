from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Document, Settings, UserBase, VerificationCode


@admin.register(Settings)
class SettingsAdmin(ModelAdmin):
    pass


@admin.register(UserBase)
class UserBaseAdmin(ModelAdmin):
    pass


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
