import mimetypes

import httpx
from auth_base.models import Avatar
from django.contrib.auth.hashers import make_password
from django.db import transaction
from google.auth.transport import requests
from google.oauth2 import id_token
from requests_oauthlib import OAuth1Session
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from finance.request_base import BaseViewSet, base_methods
from finance.serializers import AppBaseSerializer
from finance.utils import random_with_n_digits, get_profile_pic_from_url


class Social:
    TWITTER_HOST_URL = 'https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true'
    INSTAGRAM_HOST_URL = 'https://graph.instagram.com/me'
    FACEBOOK_HOST_URL = 'https://graph.facebook.com/v5.0/me'
    SOCIAL_AUTH = ['facebook', 'twitter']
    ACCEPTED_PROVIDERS = ['facebook', 'google', 'twitter']


class SocialBaseSerializer(AppBaseSerializer, Social):
    token = serializers.CharField(allow_blank=False, trim_whitespace=True, write_only=True, required=True)

    def create(self, validated_data):
        raw_data = self.get_raw_data(validated_data)
        self.set_attr(raw_data)
        cleaned_data = self.cleaned_data
        return self.create_or_update_user(cleaned_data)

    @staticmethod
    def resolve_date(date):
        from dateutil.parser import parse
        return parse(date).strftime('%Y-%m-%d')

    @staticmethod
    def generate_user_pass(data) -> dict:
        data['username'] = data['first_name'] + data['unique_id']
        data['password'] = make_password(random_with_n_digits(10))
        return data

    @staticmethod
    def create_avatar(user, url) -> Avatar:
        return Avatar.objects.create(user=user, image=get_profile_pic_from_url(url))

    def get_raw_data(self, data):
        raise NotImplementedError("get_raw_data() needs to be overridden per auth provider.")

    def set_attr(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @property
    def cleaned_data(self) -> dict:
        return self.clean()

    def clean(self):
        raise NotImplementedError("clean() needs to be overridden per auth provider.")

    @transaction.atomic()
    def create_or_update_user(self, data):
        user_query = self.Meta.model.objects.filter(unique_id=data["unique_id"])

        # Returns the first user in the user_query if user exists.
        if user_query:
            return user_query.first()

        # If user not found create and return the user.
        from auth_base.serializers import UserSerializer
        local_data = self.generate_user_pass(data)
        local_user = self.nested_create(UserSerializer, local_data)
        local_data.pop("username"), local_data.pop("password")

        if data.__contains__("avatar"):
            self.create_avatar(local_user, data["avatar"])
            data.pop("avatar")

        social_user = self.Meta.model.objects.create(association=local_user, **data)

        return social_user


class FacebookBase(SocialBaseSerializer):

    def get_raw_data(self, data):
        token = data["token"]
        fields = "first_name,last_name,email,gender,birthday,hometown"
        params = {'fields': fields, 'access_token': token, 'format': 'json', 'method': 'get',
                  'suppress_http_code': 1}
        response = httpx.get(self.FACEBOOK_HOST_URL, params=params)
        if 'error' in response.json():
            raise serializers.ValidationError('Incorrect token or sufficient permissions not provided.')
        return response.json()

    def clean(self):
        data = dict()
        data['first_name'] = self.first_name
        data['last_name'] = self.last_name
        data['unique_id'] = self.id

        data["avatar"] = f'http://graph.facebook.com/{self.id}/picture?type=large'

        if hasattr(self, "email"):
            data["email"] = self.email

        if hasattr(self, "gender"):
            data["gender"] = self.gender

        if hasattr(self, "birthday"):
            data["birth_date"] = self.resolve_date(self.birthday)

        if hasattr(self, "hometown"):
            data['city'], data['state'] = self.hometown['name'].strip().replace(" ", "").split(',')

        return data


class GoogleBase(SocialBaseSerializer):

    def get_raw_data(self, data):
        token = data["token"]
        try:
            id_info = id_token.verify_oauth2_token(token, requests.Request())
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise PermissionDenied('Wrong issuer.')
            return id_info
        except ValueError as e:
            print(e)
            raise serializers.ValidationError('Incorrect token or sufficient permissions not provided.')

    def clean(self):
        data = dict()
        data["first_name"] = self.given_name
        data["last_name"] = self.family_name
        data["unique_id"] = self.sub
        data["avatar"] = self.picture

        if hasattr(self, "email"):
            data["email"] = self.email

        return data


class TwitterBase(SocialBaseSerializer):
    secret = serializers.CharField(allow_blank=False, trim_whitespace=True, write_only=True, required=True)

    def get_raw_data(self, data):
        token = data["token"]
        secret = data["secret"]
        twitter = OAuth1Session(client_key="TWITTER_API_KEY",
                                client_secret="TWITTER_API_KEY_SECRET",
                                resource_owner_key=token,
                                resource_owner_secret=secret)
        r = twitter.get(self.TWITTER_HOST_URL)
        if 'errors' in r.json():
            raise serializers.ValidationError(r.json()['errors'][0]['message'])
        return r.json()

    def clean(self):
        data = dict()
        data['unique_id'] = self.id_str
        data['first_name'], data['last_name'] = self.name.split(" ")
        data["avatar"] = self.profile_image_url

        if hasattr(self, "email"):
            data["email"] = self.email

        return data


class BaseMediaSerializer(AppBaseSerializer):
    media_type = serializers.SerializerMethodField()

    @staticmethod
    def get_media_type(obj):
        return f'{mimetypes.guess_type(obj.file.url)[0]}'


class BaseSocialViewSet(BaseViewSet):
    http_method_names = ['post'] + base_methods
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        from auth_base.serializers import UserSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = user.token
        response_data = {'token': {'refresh': f'{token}', 'access': f'{token.access_token}'},
                         'user': UserSerializer(user.association).data}
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
