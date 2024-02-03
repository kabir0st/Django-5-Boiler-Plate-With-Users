import os
from django.conf import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
celery_app = Celery('core',
                    backend=settings.CELERY_BROKER,
                    broker=settings.CELERY_BROKER)
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
