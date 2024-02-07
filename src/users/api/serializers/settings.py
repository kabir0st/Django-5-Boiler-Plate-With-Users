from rest_framework import serializers

from users.models.settings import GeneralSettings


class SettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GeneralSettings
        fields = '__all__'
