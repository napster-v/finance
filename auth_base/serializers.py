from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.tokens import RefreshToken

from finance.request_base import read_only_social_fields
from finance.serializers import AppBaseSerializer
from auth_base.models import Avatar, AppUser, FacebookSocialUser, GoogleSocialUser, TwitterSocialUser
from auth_base.social_base import FacebookBase, GoogleBase, TwitterBase


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='avatar.image', read_only=True)
    gender_str = serializers.SerializerMethodField()

    class Meta:
        model = AppUser
        exclude = ['password', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
        read_only_fields = ['last_login', 'is_active', 'date_joined', 'username']

    @staticmethod
    def get_gender_str(obj: AppUser):
        return obj.gender_str

    @staticmethod
    def create_or_update(serializer, **kwargs):
        serializer = serializer(**kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()


class UserAvatarSerializer(AppBaseSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Avatar


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = PasswordField(required=True)

    def create(self, validated_data):
        user: AppUser = authenticate(**validated_data)
        if not user or not user.is_active:
            raise AuthenticationFailed('Username or password is incorrect.')
        return user

    def update(self, instance, validated_data):
        """
        Added to avoid ABC of python.
        :param instance:
        :param validated_data:
        :return:
        """
        pass


class LogOutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    default_error_messages = {
        'bad_token': 'Token is invalid or expired'
    }

    def create(self, validated_data):
        try:
            refresh = RefreshToken(validated_data['refresh'])
            refresh.blacklist()
        except TokenError:
            self.fail('bad_token')
        return refresh


class PasswordSerializer(serializers.Serializer):
    password = PasswordField(required=True)
    confirm_password = PasswordField(required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise ValidationError('Passwords do not match.')

        return attrs


class FacebookSerializer(FacebookBase):
    class Meta:
        model = FacebookSocialUser
        read_only_fields = read_only_social_fields


class GoogleSerializer(GoogleBase):
    class Meta:
        model = GoogleSocialUser
        read_only_fields = read_only_social_fields


class TwitterSerializer(TwitterBase):
    class Meta:
        model = TwitterSocialUser
        read_only_fields = read_only_social_fields
