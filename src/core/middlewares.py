import json
import logging

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.utils.timezone import now
from core.utils.functions import get_browser_and_os


def get_user(token):
    user = cache.get(f'{token}')
    if user:
        return user
    else:
        return AnonymousUser()


def get_device(token):
    if device := cache.get(f'device_{token}'):
        return device
    else:
        return None


# disabling caching of user info
class APIAuthenticationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff:
                pass
        else:
            token = request.headers.get("Authorization", None)
            request.user = get_user(token)
        if request.user and request.user.is_authenticated:
            cache.set(f'web_info_{request.user.id}-{token}',
                      json.dumps({
                          'uuid': token if token else 'admin_test_session',
                          'info': get_browser_and_os(request),
                          'last_activity': str(now())
                      }),
                      timeout=cache.ttl(f"{token}"))
        response = self.get_response(request)
        return response


class DisableCSRF(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "_dont_enforce_csrf_checks", True)
        response = self.get_response(request)

        return response


def core_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Exception):
        error = str(exc)
        if hasattr(exc, 'detail'):
            error = exc.detail
        if isinstance(exc, ValidationError):
            error = ' / '.join([
                f"{key.capitalize()}: {e.capitalize()}" for key in exc.detail
                for e in exc.detail[key]
            ])
        err_data = {'status': False, 'error': error}
        logging.error(f"Original error detail and call stack: {exc}",
                      exc_info=settings.DEBUG)
        return JsonResponse(err_data, safe=False, status=503)
    return response


class PaginationMiddleware(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100
