from django.contrib.auth import get_user_model
import django.apps
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django.setup()

User = get_user_model()

admin = User.objects.create_superuser('admin@admin.com', 'pass')
admin.save()
