import json
import random
import re
import ssl
import string
import subprocess
import tempfile
import urllib
import urllib.request
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from itertools import tee
from random import randint
from tempfile import NamedTemporaryFile

import requests
from PIL import Image
from dateutil.relativedelta import relativedelta
from dateutil.rrule import HOURLY, rrule
from django.core import files
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError
from django.core.files import File
from django.core.validators import (
    MaxLengthValidator, MaxValueValidator, MinLengthValidator,
    MinValueValidator,
    RegexValidator)
from django.db.models import QuerySet
from django.forms.utils import ErrorDict
from django.http import HttpResponseNotAllowed, HttpResponse
from django.utils import timezone
from django.utils.datetime_safe import date, datetime
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response

from .codes import ErrorCode


def get_data(response):
    response = {"status": True, "status_code": str(response.status_code), "status_text": response.status_text,
                "data": response.data}
    return response


def ssl_request(request_url, method=None, data=None, headers=None):
    try:
        ssl_header = {'X-Mashape-Key': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}
        if headers is None:
            headers = ssl_header
        else:
            headers.update(ssl_header)

        req = urllib.request.Request(request_url, data=data, method=method,
                                     headers=headers)
        return json.loads(urllib.request.urlopen(req, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)).read())
    except Exception as e:
        return None


def extract_post_value(request, value):
    return request.POST.get(value, None)


def extract_get_value(request, value):
    return request.GET.get(value, None)


def is_request_method_get(request):
    return check_request_method(request, "GET")


def is_request_method_post(request):
    return check_request_method(request, "POST")


def check_request_method(request, method):
    if request.method != method:
        return HttpResponseNotAllowed('Only ' + method + ' requests permitted')


def time_json(datetime):
    return json.loads(
        json.dumps({"string": str(datetime), "timestamp": int(datetime.timestamp())}))


def is_time_stale(datetime, seconds=0):
    valid_until = datetime + timedelta(seconds=seconds)
    return int(valid_until.timestamp()) < int(timezone.now().timestamp())


def value_validation(value, max, min=0, allow_none=True, field_name=None,
                     min_error_message=None, max_error_message=None, none_string_error_message=None):
    field_name = field_name if field_name != None else "value"

    if none_string_error_message == None:
        none_string_error_message = field_name + " can't be empty"

    if value == None:
        if not allow_none:
            raise Exception(none_string_error_message)
        return value

    if max_error_message == None:
        max_error_message = "Incorrect " + field_name + ". Max value of " + str(max) + " is allowed."

    if min_error_message == None:
        min_error_message = "Incorrect " + field_name + ". Required MIN value is " + str(min) + "."

    MinValueValidator(min, min_error_message)(value)
    MaxValueValidator(max, max_error_message)(value)

    return value


def string_length_validation(string, max_length, min_length=0, allow_none=True, field_name=None,
                             min_error_message=None, max_error_message=None, none_string_error_message=None):
    field_name = field_name if field_name != None else "value"

    if none_string_error_message == None:
        none_string_error_message = field_name + " can't be empty"

    if string == None:
        if not allow_none:
            raise Exception(none_string_error_message)
        return string

    if max_error_message == None:
        max_error_message = "Incorrect " + field_name + " length. Max length " + str(
            max_length) + " is allowed."

    if min_error_message == None:
        min_error_message = "Incorrect " + field_name + " length. Required MIN length is " + str(
            min_length) + "."

    MaxLengthValidator(max_length, max_error_message)(string)
    MinLengthValidator(min_length, min_error_message)(string)

    return string


def get_timestamp_to_timezone(millis):
    try:
        return timestamp_to_timezone(millis)
    except:
        return None


def timestamp_to_timezone(epoch_seconds):
    if epoch_seconds == None:
        raise Exception("None not allowed")
    return timezone.make_aware(datetime.utcfromtimestamp(int(epoch_seconds // 1000)), timezone.utc)


def image_name(file):
    return str(uuid.uuid4()) + "." + str(Image.open(file).format).lower()


def file_download(url) -> File:
    # Steam the image from the url
    request = requests.get(url, stream=True)

    # Was the request OK?
    if request.status_code != requests.codes.ok:
        raise Exception("Something went wrong")

    # Create a temporary file
    lf = tempfile.NamedTemporaryFile()

    # Read the streamed image in sections
    for block in request.iter_content(1024 * 8):

        # If no more file then stop
        if not block:
            break

        # Write image block to temporary file
        lf.write(block)

    return files.File(lf)


def video_file_size(value):
    file_size(value, 50000)


def image_file_size(value):
    file_size(value, 5000)


def file_size(value, kb: int):
    limit = kb * 1024
    if value.size > limit:
        raise ValidationError(
            "File too large(" + str(value.size / 1024) + " Kb). Size should not exceed " + str(
                limit / 1024) + "  Kb.")


def __request_response_success(data):
    return {"data": data}


def __request_response_error(error_code: ErrorCode, fields: dict = None, message: str = None):
    fields_array = []

    if fields is not None:
        for key, value in fields.items():
            fields_array.append({"field": key, "message": value})

    return Response({"error": {
        "message": message,
        "status": error_code.get_http_status_code(),
        "error": error_code.phrase,
        "error_code": error_code.value,
        "description": error_code.description,
        "fields": fields_array
    }})


def request_http_error_response(error_code: ErrorCode, fields: dict = None, message: str = None) -> HttpResponse:
    if message is None:
        if error_code.is_FIELDS_ERROR() and fields is not None:
            message = 'Error in "{}" field.'.format(len(fields))
        else:
            message = error_code.description

    return (__request_response_error(error_code, fields, message=message),
            error_code.get_http_status_code())


def request_http_response_created(data) -> HttpResponse:
    return request_http_response(data, 201)


def request_http_response(data, status_code=200) -> HttpResponse:
    return JsonHttpResponse(__request_response_success(data), status_code)


def empty_response() -> HttpResponse:
    return HttpResponse(status=204)


def JsonHttpResponse(serialize_data, status_code=200) -> HttpResponse:
    return HttpResponse(serialize_to_json(serialize_data), content_type="json", status=status_code)


def unknown_error_response(message="") -> HttpResponse:
    return HttpResponse(status=500, content=message)


def serialize_to_json(data):
    return json.dumps(data)


class CallBack():
    def callback(self, call):
        pass

    @staticmethod
    def iterate_list(items: list, callback):

        """
        my_method description

        @type items: list
        @param items: A List

        @:type callback: CallBack
        @:param callback: CallBack

        @rtype: string
        @return: Returns a sentence with your variables in it
        :param callback:
        """

        try:
            for item in items:
                callback.callback(item)
        except Exception as e:
            print(str(e))


class RequestParaHelper:
    __mandatory_fields = []

    def __init__(self):
        self.__mandatory_fields.clear()
        self.__mandatory_fields.extend(RequestParaHelper.get_mandatory_params())

    @staticmethod
    def get_mandatory_params():
        return []


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def generate_token():
    return uuid.uuid4()


def random_string(string_length=25):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


def plural(count: int, singular_word: str, plural_word: str) -> str:
    if count > 1:
        return plural_word
    return singular_word


def validation_error_extraction(error: ValidationError):
    str = ""
    for err in error.messages:
        str += err
    return str


def form_error(error_dict: ErrorDict, field_name: str):
    err = (error_dict.get(field_name, "--not found--") or [None])[0]
    return validation_error_extraction(err)


def require_non_none(value, non_none_value):
    if value is None:
        return non_none_value
    return value


def to_minutes(minutes=1):
    return minutes * 60


def to_hours(hours=1):
    return hours * to_minutes(60)


def to_days(days=1):
    return days * to_hours(24)


def validate_gender(gender):
    if gender is not None:
        try:
            return gender
        except:
            raise Exception("unknown gender found")


def is_gender_valid(gender) -> bool:
    try:
        validate_gender(gender)
        return True
    except:
        return False


COUNTRY = (('India', 'India'),
           ('Other', 'Other')
           )
STATE = (
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Orissa', 'Orissa'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli', 'Dadra and Nagar Haveli'),
    ('Daman and Diu', 'Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
    ('Other', 'Other')
)

GENDER = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Others', 'Others')
)


def validate_char_number(string, max_length, field_name=None, allow_none=True):
    string = string_length_validation(string, max_length, 1, field_name=field_name,
                                      allow_none=allow_none)
    if string is not None:
        if re.match("^[\w\d_-]+$", string):
            return string
        else:
            raise Exception("Invalid " + str(field_name) + " format")


def validate_char(string, max_length, field_name=None, allow_none=True):
    string = string_length_validation(string, max_length, 1, field_name=field_name,
                                      allow_none=allow_none)
    if string is not None:
        if re.match("^[A-Za-z-]+$", string):
            return string
        else:
            raise Exception("Invalid " + str(field_name) + " format")


def settings_add_db(db_name: str):
    settings.DATABASES.update({db_name: {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': db_name,
        'USER': 'g10consultancy',
        'PASSWORD': 'GTEN@10',
        'HOST': 'localhost',
        'PORT': '5432',
    }})
    print("databases: ", settings.DATABASES)


size = 128, 128


def compress_image(image):
    im = Image.open(image)
    output = BytesIO()
    # Resize/modify the image
    im = im.convert('RGB')
    print(im.mode)
    from PIL import ImageFilter
    im = im.filter(ImageFilter.EDGE_ENHANCE)
    im = im.filter(ImageFilter.SMOOTH)
    im = im.resize((im.width // 2, im.height // 2))
    # im.save(BASE_DIR + file_url, format='JPEG', quality=60, optimize=True, progressive=True)
    # convert to jpg
    # after modifications, save it to original file
    im.save(output, format='JPEG', quality=60, optimize=True, progressive=True)
    name = ''.join(random_string()) + ".jpg"
    print(name)
    compressed_image = File(output, name=name)
    return compressed_image


def get_thumbnail(image):
    im = Image.open(image)
    output = BytesIO()
    im = im.convert('RGB')
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(output, format='JPEG')
    name = ''.join(random_string()) + ".jpg"
    thumbnail_image = File(output, name=name)
    return thumbnail_image


def compress_video(sender, instance, **kwargs):
    subprocess.check_call(
        ["ffmpeg-git-20190807-amd64-static/ffmpeg", "-i", "" + instance.video.path + "", "-c:v", "libx265", "-crf",
         "28", "-c:a", "aac",
         "-b:a", "128k", "Media/videos/tmp/" + instance.video.name + ""])
    subprocess.check_call(["mv", "Media/videos/tmp/" + instance.video.name + "", "" + instance.video.path + ""])
    # ffmpeg -i input -c:v libx265 -crf 28 -c:a aac -b:a 128k output.mp4


mobile: RegexValidator = RegexValidator(regex=r'^[987]+\d{9}$',
                                        message="Phone number must be entered in the format: '9876543210'.10 digits allowed.")


def compare_start_end_time_validation(start_time, end_time=None):
    if end_time and start_time > end_time:
        raise ValidationError("Can't set end time before start time.")


def compare_date_validation(start_date, end_date=None):
    if end_date and start_date > end_date:
        raise ValidationError("Can't set end date before start date.")


def compare_date_time_validation(start_date_time, end_date_time=None):
    if end_date_time and start_date_time > end_date_time:
        raise ValidationError("Can't set end time before start time.")


def future_date_time_validation(value, field_name='Date time'):
    now = timezone.now()
    if value < now:
        raise ValidationError(field_name + ' cannot be in the past.')


def past_date_time_validation(value, field_name='Date time'):
    now = timezone.now()
    if value > now:
        raise ValidationError(field_name + ' cannot be in the future.')


def future_date_validation(value, field_name='Date'):
    today = date.today()
    if value < today:
        raise ValidationError(field_name + ' cannot be in the past.')


def past_date_validation(value, field_name='Date'):
    today = date.today()
    if value > today:
        raise ValidationError(field_name + ' cannot be in the future.')


def date_of_birth_validation(value):
    past_date_validation(value, "date_of_birth")


def date_of_anniversary_validation(value):
    past_date_validation(value, "date_of_anniversary")


def add_days(value, days):
    return value + relativedelta(days=days)


MEDIA_PATH = 'media/images/%Y/%m/%d/'
MEDIA_PATH_THUMBS = 'media/thumbnails/%Y/%m/%d/'
MEDIA_PATH_VIDEO = 'media/videos/%Y/%m/%d/'
VIDEO_THUMBS = 'media/video_thumbs/%Y/%m/%d/'
_requests = {}


def remove_duplicates(args):
    return list(dict.fromkeys(args))


# def create_user_specific_db(dbname: str):
#     con = None
#     con = psycopg2.connect(dbname='postgres', user='postgres', host='localhost', password='123')
#     con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cur = con.cursor()
#     cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}' ".format(dbname))
#     cur.execute('CREATE DATABASE "{}" WITH TEMPLATE "{}"'.format(dbname, settings.DATABASES_CM_DB))
#     cur.execute('GRANT ALL PRIVILEGES ON DATABASE "{}" TO g10consultancy'.format(dbname))
#     cur.close()
#     con.close()
#     settings_add_db(dbname)
#
#
# def drop_db(dbname: str):
#     con = None
#     con = psycopg2.connect(dbname='postgres', user='postgres', host='localhost', password='')
#     con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cur = con.cursor()
#     cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}' ".format(dbname))
#     cur.execute(f'DROP DATABASE "{dbname}"')
#     cur.close()
#     con.close()
#
#
# def drop_db_alternate(dbname: str):
#     con = None
#     con = psycopg2.connect(dbname='postgres', user='postgres', host='localhost', password='')
#     con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cur = con.cursor()
#     cur.execute(f'SELECT * FROM pg_stat_activity WHERE datname={dbname}')
#     cur.execute(
#         f'SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname={dbname}')
#     cur.execute(f'DROP DATABASE {dbname};')
#     cur.close()
#     con.close()
#     settings_add_db(dbname)


def str_choice_validation(choices: tuple, value_name, value):
    if value is not None:
        choice_validation(choices, value_name, value.capitalize())
        return value.capitalize()


def choice_validation(choices: tuple, value_name, value):
    from rest_framework.exceptions import ValidationError
    try:
        serializers.ChoiceField(choices=choices).run_validation(value)
    except ValidationError as e:
        values = ''.join('{}, '.format(val) for key, val in sorted(dict((y, x) for x, y in choices).items()))
        raise serializers.ValidationError(
            _("Invalid " + value_name + " selected, select one of (" + values + ")"))
    except Exception as e:
        raise serializers.ValidationError(_(str(e)))


class SuccessApiJSONRenderer(BaseRenderer):
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context: dict = None):
        response: Response = renderer_context.get('response')

        try:
            page_data = data.get("data")
            if page_data is not None:
                return json.dumps(data)
        except:
            pass
        # Do we really need this since DRF return 204 empty response?ToDo
        if response.status_code == 204:
            return b''

        response_dict = {'data': []}
        if data:
            response_dict['data'] = data
        data = response_dict
        return json.dumps(data)


class SuccessAPIRenderer(BaseRenderer):
    media_type = 'application/json'
    format = 'json'

    def render(self, data: dict, accepted_media_type=None, renderer_context: dict = None):
        if data is not None:
            if data.__contains__('error'):
                return json.dumps(data)
            elif data.__contains__('data'):
                return json.dumps(data)
            else:
                return json.dumps({"data": data})
        return b''


def choices(model, choices: dict, field_name='name'):
    queryset: QuerySet = model.objects.all()
    if queryset.exists():
        return queryset
    for value in choices:
        kwargs = {'%s' % field_name: value}
        model.objects.create(**kwargs)

    return model.objects.all()


def tuple_choices(model, tuple_choice: tuple, field_name='name'):
    query_set: QuerySet = model.objects.all()
    if query_set.exists():
        return query_set

    for key, value in tuple_choice:
        kwargs = {'%s' % field_name: value}
        model.objects.create(**kwargs)

    return model.objects.all()


def resolve_status(start):
    from datetime import date
    today = date.today()
    if start > today:
        return 1  # Upcoming
    return 2  # OnGoing


def get_profile_pic(temp):
    r = requests.get(f'http://graph.facebook.com/{temp}/picture?type=large')
    image = NamedTemporaryFile(delete=True)
    image.write(r.content)
    image.flush()
    image.name = f'{random_string(string_length=10)}.jpeg'
    return File(image)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def get_time_slot_pairs(start, end):
    """
    Takes in start_time / end_time and returns pairs of time. ABCD -> AB BC CD
    """
    rule = rrule(dtstart=start, until=end, freq=HOURLY)
    data = pairwise(rule)
    return data


def youtube_url_validator(value):
    result = re.search('^https://yout{1}', value)
    if not result:
        raise ValidationError('Provided URL is not a valid YouTube link.')

def get_profile_pic_from_url(url):
    r = requests.get(url)
    image = NamedTemporaryFile(delete=True)
    image.write(r.content)
    image.flush()
    image.name = f'{random_string(string_length=10)}.jpeg'
    return File(image)
