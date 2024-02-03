import json

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.forms import ValidationError
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils.functions import get_browser_and_os, is_token_valid
from users.api.serializers.userbase import UserBaseSerializer
from users.models import UserBase, VerificationCode


def set_token_to_cache(tokens, user):
    cache.set(
        tokens["access"],
        user,
        settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
    )
    cache.set(
        tokens["refresh"],
        user,
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
    )
    cache.set(
        f'refresh_{tokens["access"]}',
        tokens['refresh'],
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
    )


def remove_tokens_from_cache(access_token, user_id):
    cache.delete(f'{access_token}')
    refresh = cache.get(f'refresh_{access_token}')
    cache.delete(refresh)
    cache.delete(f'refresh_{access_token}')
    cache.delete(f'web_info_{user_id}-{access_token}', )


def generate_token(user, request=None):
    tokens = RefreshToken.for_user(user)
    tokens = {"access": str(tokens.access_token), "refresh": str(tokens)}
    set_token_to_cache(tokens, user)
    details = UserBaseSerializer(instance=user).data
    if not user.is_active:
        user.is_active = True
        user.save()
        user.update_cache(tokens.access_token)
    cache.set(
        f'web_info_{request.user.id}-{tokens["access"]}',
        json.dumps({
            'uuid': tokens['access'],
            'info': get_browser_and_os(request),
            'last_activity': str(now())
        }))
    return (tokens, details)


def authenticate_user(email, password, request):
    user = authenticate(email=email, password=password)
    if not user:
        raise Exception("Email or password wrong.")
    return generate_token(user, request)


@api_view(["POST", "GET"])
def login(request):
    """
    Returns a JWT token.
    {
        'email'- __str__,
        'password'- __str__
    }
    """
    if request.method == "GET":
        return Response({'msg': 'For testing.'})
    email = str(request.data["email"])
    password = str(request.data["password"])
    # does not check password before activating the account
    if old_user := UserBase.objects.filter(email=email).first():
        if not old_user.is_active:
            old_user.is_active = True
            old_user.save()
    if request.device:
        user = authenticate(email=email, password=password)
        if not user:
            raise Exception("Email or password wrong.")
        if not user.is_active:
            user.is_active = True
            user.save()
        request.device.user = user
        request.device.last_activity = now()
        request.device.save()
        return Response({
            'status': True,
            'user': UserBaseSerializer(user).data
        })
    token, details = authenticate_user(email, password, request)
    return Response({"tokens": token, "user": details, "status": True})


@api_view(["GET"])
def whoami(request):
    response = {}
    if request.user.is_authenticated:
        response['user'] = UserBaseSerializer(instance=request.user).data
        token = request.headers.get("Authorization", None)
        if token:
            response['web'] = cache.get(f'info_{request.user.id}-{token}')
    if response:
        return Response(response, status=status.HTTP_200_OK)
    else:
        return Response({"msg": "Anonymous User."},
                        status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_refresh(request):
    """
    {
        "refresh": "refresh_token"
    }
    """
    data = request.data
    if not is_token_valid(data["refresh"]):
        raise Exception("Passed refresh is blacklisted. Try logging in.")
    user = cache.get(f'{data["refresh"]}')
    x = TokenRefreshSerializer(data=data)
    try:
        x.is_valid(raise_exception=True)
    except Exception as e:
        raise Exception(e.args[0]) from e
    tokens = {
        "access": x.validated_data["access"],
        "refresh": x.validated_data["access"],
    }
    cache.delete(data["refresh"])
    set_token_to_cache(tokens, user)
    return Response(tokens, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Invalidates current JWT token.


    Call Logout after user logs out and also remember to delete the token from
    local storage.

    """
    if token := request.headers.get("Authorization", None):
        remove_tokens_from_cache(token, request.user.id)
    if request.device:
        request.device.user = None
        request.device.save()
    return Response({"status": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """
    {
        "email": "<EMAIL>",
        "code": "<CODE>",
        "password": "<PASSWORD>"
    }
    """
    password = request.data['password']
    code = request.data['code']
    obj = VerificationCode.objects.filter(email=request.data['email'],
                                          otp_for='password_reset').first()
    if obj is None:
        raise ValidationError(
            "No verification code was generated for password reset.")
    res, msg = obj.check_code(code)
    if res:
        user = UserBase.objects.get(email=obj.email)
        user.set_password(password)
        user.save()
        return Response({'status': True})
    return Response({'msg': msg})


@api_view(["POST"])
@permission_classes([AllowAny])
def forget_password(request):
    """
    {
        "email": "<EMAIL>"
    }
    """
    try:
        user = UserBase.objects.get(email=request.data['email'])
        VerificationCode.generate(user, 'password_reset')
        return Response({'status': True})
    except Exception as e:
        raise APIException('User does not exists.') from e


@api_view(["POST"])
@permission_classes([AllowAny])
def provider_login(request):
    """
    send google user access token.
    {
        'token': __str__
    }
    """
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"alt": "json", "access_token": request.data["access_token"]}
    headers = {
        "Authorization": f"Bearer {request.data['access_token']}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {e}")
    if data:
        if UserBase.objects.filter(email=data['email']).exclude(
                provider='google').first():
            raise ValidationError(
                'The email address has already been utilized to'
                ' establish an account with a password. '
                'Kindly log in using the email and password.')
        user, created = UserBase.objects.get_or_create(
            email=data['email'], provider_uuid=data['id'], provider='google')
        if created:
            user.is_verified = True
            user.given_name = data['given_name']
            user.family_name = data['family_name']
            user.save()
        tokens = generate_token(user, request)
        return Response(tokens)
    return Response(
        {"msg": "Error getting data from google from given token."},
        status=status.HTTP_400_BAD_REQUEST)
