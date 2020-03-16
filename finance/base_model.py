from django.db import models

from finance import settings

MEDIA_PATH = settings.MEDIA_PATH
MEDIA_PATH_VIDEO = settings.MEDIA_PATH_VIDEO
CHAR_FIELD_MAX_LENGTH = 100


class AppBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True, null=True)
    deleted = models.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True


class BaseMedia(AppBaseModel):
    name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=MEDIA_PATH, null=True, blank=True)

    class Meta:
        abstract = True
