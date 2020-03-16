from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from rest_framework_simplejwt.tokens import RefreshToken

from finance.base_model import AppBaseModel, MEDIA_PATH, CHAR_FIELD_MAX_LENGTH


# Create your models here.


class AppUser(AbstractUser):
    class Gender(models.TextChoices):
        Male = 1, 'MALE'
        Female = 2, 'FEMALE'
        TransGender = 3, 'TRANSGENDER'
        Other = 4, 'OTHER'

    anniversary_date = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True)
    gender = models.CharField(max_length=15, choices=Gender.choices, blank=True)
    married = models.NullBooleanField()
    age = models.PositiveSmallIntegerField(blank=True, null=True)

    @property
    def info(self):
        from auth_base.serializers import UserSerializer
        return UserSerializer(self).data

    @property
    def token(self):
        return RefreshToken.for_user(self)

    @property
    def has_avatar(self):
        try:
            self.avatar
            return True
        except ObjectDoesNotExist:
            return False

    @property
    def has_social(self):
        try:
            self.socialprofile
            return True
        except ObjectDoesNotExist:
            return False

    def remove_avatar(self):
        if self.has_avatar:
            self.avatar.delete()
        return self

    @property
    def gender_str(self):
        if isinstance(self.get_gender_display(), str):
            return self.get_gender_display().upper()
        return f''

    def clean(self):
        self.password = make_password(self.password)


class Avatar(AppBaseModel):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=MEDIA_PATH)


class BaseSocialUser(AppBaseModel):
    association = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    first_name = models.CharField(null=True, blank=True, max_length=CHAR_FIELD_MAX_LENGTH)
    last_name = models.CharField(null=True, blank=True, max_length=CHAR_FIELD_MAX_LENGTH)
    email = models.EmailField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    gender = models.CharField(null=True, blank=True, max_length=CHAR_FIELD_MAX_LENGTH)
    unique_id = models.DecimalField(null=True, blank=True, max_digits=25, decimal_places=0)

    class Meta:
        abstract = True

    @property
    def token(self):
        return self.association.token


class FacebookSocialUser(BaseSocialUser):
    pass


class GoogleSocialUser(BaseSocialUser):
    pass


class TwitterSocialUser(BaseSocialUser):
    pass
