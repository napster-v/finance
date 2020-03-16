from rest_framework import serializers
from rest_framework.fields import empty

import mimetypes

from finance.base_model import AppBaseModel


class AppBaseSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        # read_only_fields: list = getattr(self.Meta, 'fields', None)
        exclude: list = getattr(self.Meta, 'exclude', None)
        fields: list = getattr(self.Meta, 'fields', None)
        # exclude AppBaseModel fields
        base_fields = [f.name for f in AppBaseModel._meta.fields]
        if exclude:
            for x in base_fields:
                exclude.append(x)
            exclude = list(dict.fromkeys(exclude))
        elif not fields:
            exclude = list(dict.fromkeys(base_fields))
        self.Meta.exclude = exclude

    def get_user(self):
        """
        We can define this in a serializer and inherit that serializer.
        :return: User object
        """
        user = self.context.get("request").user
        return user

    @staticmethod
    def nested_create(serializer, data, **kwargs):
        serializer = serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(**kwargs)

    @staticmethod
    def nested_update(instance, serializer, data, **kwargs):
        serializer = serializer(data=data, instance=instance, partial=True)
        serializer.is_valid(raise_exception=True)
        return serializer.save(**kwargs)

    @staticmethod
    def create_many_to_many(model, data: dict, parent_value):
        """
        We're using a queryset here and not serializer as data is already validated by the parent serializer.
        Also when you try to call 'is_valid' on a serializer it throws an error that it requires a pk value.
        If we supply value, the object won't get created as django create query is run in the background and
        it requires instance and not pk value.

        @rtype: Model
        """
        model.objects.create(related=parent_value, **data)

    def get_request(self):
        return self.context.get('request')

    @property
    def _request(self):
        return self.get_request()

    def nested_update_data(self, instance, serializer, data):
        if data:
            if not instance:
                return self.nested_create(serializer, data)
            elif data:
                serializer = serializer(instance, data=data, partial=self.partial, context=self.context)
                serializer.is_valid(raise_exception=True)
                return serializer.save()


class BaseMediaSerializer(AppBaseSerializer):
    media_type = serializers.SerializerMethodField()

    def get_media_type(self, obj):
        return f'{mimetypes.guess_type(obj.file.url)[0]}'
