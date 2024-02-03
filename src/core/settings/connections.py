import os

from .environments import (DB_NAME, DB_PASSWORD, DB_USERNAME, PREFIX_KEY,
                           channel, DOCKER)

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

REDIS_HOST = '127.0.0.1'
DATABASE_HOST = '127.0.0.1'

if DOCKER:
    REDIS_HOST = 'redis'
    DATABASE_HOST = 'db'

REDIS_URL = f"redis://{REDIS_HOST}:6379/{channel}"

CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER = REDIS_URL
SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "app.urls.api_info",
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": PREFIX_KEY,
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": DB_NAME,
        "USER": DB_USERNAME,
        "PASSWORD": DB_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": 5432,
    }
}
if os.environ.get("GITHUB_WORKFLOW"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "github_actions",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }
