import copy
from collections import Counter

from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, MethodNotAllowed, NotFound, NotAuthenticated, \
    ValidationError, PermissionDenied
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken

from .request_base import base_methods
from .codes import ErrorCode


class InvalidHeaderToken(InvalidToken):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Token is invalid or expired'
    default_code = 'token_not_valid'


def invalid_token(exc, context, *args):
    response = exception_handler(exc, context)
    if response is not None:
        message = exc.detail['detail']
        response.data.clear()
        error = args.__getitem__(0)
        error_dict = {'message': message, 'status': response.status_code, 'error': error.phrase,
                      'error_code': error.value, 'description': error.description}
        response.data['error'] = error_dict
    return response


def on_missing_fields(exc, context, *args):
    response = exception_handler(exc, context)
    if response is not None:
        error = args.__getitem__(0)
        fields_array = [{"field": key, "message": value} for key, value in args.__getitem__(1).items()]
        response.data.clear()
        error_dict = {'message': f'Error in {len(fields_array)} fields.', 'status': response.status_code,
                      'error': error.phrase, 'error_code': error.value, 'description': error.description,
                      'fields': fields_array}
        response.data['error'] = error_dict
    return response


def generate_exception(exc, context, **kwargs):
    methods = []
    response = exception_handler(exc, context)
    if response is not None:
        exception = copy.deepcopy(exc)
        response.data.clear()
        response.data = {}
        error = kwargs.get("code", None)
        view = kwargs.get("view", None)
        if view is not None:
            methods = list(Counter([x.upper() for x in view if view is not None]) - Counter(base_methods))
        message = f'Only {methods} request method/s permitted.' if methods else f'{exception}'
        error_dict = {'message': message, 'status': response.status_code, 'error': error.phrase,
                      'error_code': error.value,
                      'description': error.description}
        response.data.clear()
        response.data['error'] = error_dict
    return response


def validation_error(exc, context, **kwargs):
    response = exception_handler(exc, context)
    if response is not None:
        exception = copy.deepcopy(exc)
        response.data.clear()
        response.data = dict(response.data)
        error = kwargs.get('code', None)
        if len(exception.detail) < 2:
            message = exception.detail[0]
        else:
            message = exception
        error_dict = {'message': message, 'status': response.status_code, 'error': error.phrase,
                      'error_code': error.value, 'description': error.description}
        response.data['error'] = error_dict
    return response


def custom_exception_handler(exc, context):
    if isinstance(exc, InvalidToken):
        response = invalid_token(exc, context, ErrorCode.EXPIRED_OR_INVALID_TOKEN)
    elif isinstance(exc, MethodNotAllowed):
        response = generate_exception(exc, context, code=ErrorCode.INVALID_METHOD,
                                      view=context.get('view').http_method_names)
    elif isinstance(exc, IntegrityError):
        response = generate_exception(exc, context, code=ErrorCode.INTEGRITY_ERROR)
    elif isinstance(exc, NotFound) or isinstance(exc, Http404):
        response = generate_exception(exc, context, code=ErrorCode.NOT_FOUND)
    elif isinstance(exc, AuthenticationFailed):
        response = generate_exception(exc, context, code=ErrorCode.AUTH_FAILED)
    elif isinstance(exc, NotAuthenticated):
        response = generate_exception(exc, context, code=ErrorCode.AUTH_TOKEN_NOT_FOUND)
    elif isinstance(exc, PermissionDenied):
        response = generate_exception(exc, context, code=ErrorCode.NOT_PERMITTED)
    elif isinstance(exc, ValidationError) and isinstance(exc.detail, dict):
        response = on_missing_fields(exc, context, ErrorCode.FIELDS_ERROR, exc.detail)
    elif isinstance(exc, ValidationError):
        response = validation_error(exc, context, code=ErrorCode.VALIDATION_ERROR)
    else:
        response = generate_exception(exc, context, code=ErrorCode.INTERNAL_ERROR)

    return response
