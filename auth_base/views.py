from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from finance.request_base import MultiSerializerViewSet
from auth_base.serializers import *
from auth_base.social_base import BaseSocialViewSet

base_methods = ['head', 'options', 'trace']


# Create your views here.

class UserViewSet(MultiSerializerViewSet):
    """
    create:API NOT FUNCTIONAL
    list:List of all users
    retrieve:Get a user's info
    """
    http_method_names = ['post', 'patch', 'get'] + base_methods
    queryset = AppUser.objects.all()
    serializer_class = {
        "default": UserSerializer,
        "login": LoginSerializer,
        "logout": LogOutSerializer,
        "update_avatar": UserAvatarSerializer,
        "set_password": PasswordSerializer
    }

    @action(detail=False, methods=['post'], permission_classes=(AllowAny,))
    def login(self, request):
        """
        Takes in username and password and returns access and refresh token along with user information. Refer 100 Days.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: AppUser = serializer.save()
        headers = self.get_success_headers(serializer.data)
        token = user.token
        data = {'token': {'refresh': f'{token}', 'access': f'{token.access_token}'},
                'user': user.info}
        return Response(data, status=status.HTTP_200_OK, headers=headers)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Send the token to blacklist it and logout
        :param request:
        :return:
        """
        serializer = LogOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def update_avatar(self, request, pk=None):
        with transaction.atomic():
            self.get_object().remove_avatar()
            serializer = UserAvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=self.get_object())
            return Response(UserAvatarSerializer(instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def set_password(self, request, pk=None):
        user: AppUser = self.get_object()
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user.set_password(serializer.data['password'])
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def authenticate(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class FacebookSocialLoginViewSet(BaseSocialViewSet):
    queryset = FacebookSocialUser.objects.all()
    serializer_class = FacebookSerializer


class GoogleSocialLoginViewSet(BaseSocialViewSet):
    queryset = GoogleSocialUser.objects.all()
    serializer_class = GoogleSerializer


class TwitterSocialLoginViewSet(BaseSocialViewSet):
    queryset = TwitterSocialUser.objects.all()
    serializer_class = TwitterSerializer
