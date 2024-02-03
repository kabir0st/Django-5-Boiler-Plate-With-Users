import json

from django.core.cache import cache
from django.forms import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.utils.viewsets import DefaultViewSet
from users.models import UserBase
from users.models import VerificationCode

from .auth import authenticate_user, remove_tokens_from_cache
from .serializers import RegisterUserBaseSerializer, UserBaseSerializer


class RegisterUserBaseAPI(GenericAPIView):
    serializer_class = RegisterUserBaseSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", "get"]
    queryset = UserBase.objects.none()

    def get(self, request, *args, **kwargs):
        return Response({'msg': 'For testing'})

    def post(self, request, *args, **kwargs):
        if UserBase.objects.filter(email=request.data['email']).first():
            raise ValidationError("Email already in use.")
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if obj := VerificationCode.objects.filter(email=user.email):
                obj.delete()
            VerificationCode.generate(email=user.email,
                                      otp_for='email_verification')
            res = authenticate_user(request.data['email'],
                                    request.data['password'], request)
            return Response(res)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBaseAPI(DefaultViewSet):
    serializer_class = UserBaseSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["given_name", 'family_name', 'email']
    http_method_names = ["get", "patch", "delete", "post"]

    def create(self, request):
        return Response({'msg': 'Bad Request Method'},
                        status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserBase.objects.filter().order_by('-id')
        return UserBase.objects.filter(id=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        if token := request.headers.get("Authorization", None):
            instance.update_cache(token)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=True)
    def delete_account(self, request, *args, **kwargs):
        instance = self.get_object()
        if token := request.headers.get("Authorization", None):
            remove_tokens_from_cache(token, instance.id)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if token := request.headers.get("Authorization", None):
            instance.update_cache(token)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True)
    def sessions(self, request, *args, **kwargs):
        obj = self.get_object()
        search = f"web_info_{obj.id}-*"
        data = cache.keys(search)
        web = []
        for value in data:
            web.append(json.loads(cache.get(value, {})))
        return Response({"web": web})

    @action(methods=['get', 'post'], detail=True)
    def remove_access(self, request, *args, **kwargs):
        """
            For removing access of mobile device:
            {
                "device_type": "mobile",
                "device_id": 1 #device id
            }

            For removing access of web device:
            {
                "device_type": "web",
                "device_id": "uuid" #web device uuid
            }
        """
        if request.method == 'GET':
            return Response({"msg": "GET for testing."})
        obj = self.get_object()
        if request.data['device_type'] == "web":
            token = request.data['device_id']
            user = cache.get(f'{token}', None)
            if user is None:
                remove_tokens_from_cache(token, request.user.id)
                msg = ('Given device uuid as already been removed or '
                       'has already expired.')
                return Response({'msg': msg})
            if obj != user:
                raise ValidationError('Invalid user for the requested device.')
            remove_tokens_from_cache(token, request.user.id)
        return Response({
            'msg':
            f"Access to given {request.data['device_type']} has been device"
            " removed."
        })

    @action(methods=['get'], detail=True)
    def verify_email(self, request, *args, **kwargs):
        """
        ?code=__verification_code__
        """
        user = self.get_object()
        code = request.GET.get('code', None)
        if user.is_verified:
            return Response({"msg": "User is already verified."})
        obj = VerificationCode.objects.get(email=user.email,
                                           otp_for='email_verification')
        res, msg = obj.check_code(code)
        if res:
            user.is_verified = True
            user.save()
            obj.delete()
            if token := request.headers.get("Authorization", None):
                user.update_cache(token)
            return Response({"msg": "Email verified."})
        return Response({"msg": msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True)
    def resend_verification_email(self, request, *args, **kwargs):
        user = self.get_object()
        codes = VerificationCode.objects.filter(email=user.email,
                                                otp_for='email_verification')
        if codes:
            codes.delete()
        VerificationCode.generate(email=user.email,
                                  otp_for='email_verification')
        return Response({"msg": "Resend Verification code to email."})

    @action(methods=['post'], detail=True)
    def change_password(self, request, *args, **kwargs):
        """
        {
            "old_password": "<old_password>",
            "new_password": "<new_password>"
        }
        """
        user = self.get_object()
        if not user.check_password(request.data['old_password']):
            return Response({"msg": "Old password is incorrect."})
        user.set_password(request.data['new_password'])
        user.save()
        if token := request.headers.get("Authorization", None):
            user.update_cache(token)
        return Response({"msg": "Password Updated."})
