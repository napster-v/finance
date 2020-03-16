from enum import IntEnum
from http import HTTPStatus

__all__ = ['ErrorCode']


# noinspection PyInitNewSignature,PyTypeChecker
class ErrorCode(IntEnum):
    def __new__(cls, value, phrase, description=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.phrase = phrase
        obj.description = description
        return obj

    USER_NOT_FOUND = 1, "User not found", "Requested user not found."
    CODE_NOT_FOUND = 11, "Code not found", "The code requested does not exists or has already used."
    ACCOUNT_SUSPENDED = 2, "User suspended", "The user account has been suspended and information cannot be retrieved"
    USER_LOCKED_OUT = 3, "User locked out", "The user account has been locked out and information cannot be retrieved"
    USER_LOCKING_OUT_WARNING = 4, "User locking out warning", "The user account is at risk of locking out"
    ACCOUNT_SUSPENSION_WARNING = 5, "User suspension warning", "The user account is at risk of suspension"
    EXPIRED_OR_INVALID_TOKEN = 6, "Invalid or expired token", "The access token used in the request is incorrect or " \
                                                              "has expired. "
    AUTH_TOKEN_EXPIRED = 9, "Auth token expired", "Authorization failed."
    AUTH_TOKEN_NOT_FOUND = 7, "Auth token not found", "Please provide access token in the header. Ex. Bearer {token}."
    AUTH_FAILED = 22, "Authentication Failed", "Failed to authenticate this query."

    INVALID_AUTH_TOKEN = 10, "Invalid auth token", "Token provided is not valid."
    INVALID_REFRESH_TOKEN = 23, "Invalid refresh token", "Refresh Token provided is not valid."
    EMAIL_ALREADY_EXISTS = 15, "Email already exists", "Email provided already exists with different account."
    INVALID_METHOD = 18, "Invalid method", "Method requested in invalid. Check the API docs."
    INTERNAL_ERROR = 20, "Internal error", "Something went wrong on our side."
    FIELDS_ERROR = 21, "Fields error", "Fields error."
    NOT_PERMITTED = 24, "Not permitted", "User not permitted to perform this action."
    NOT_FOUND = 25, "Not Found", "Object not found. The resource you are looking for does not exist or is deleted."
    INTEGRITY_ERROR = 26, "DB Integrity Issue", ""
    VALIDATION_ERROR = 27, "Validation Error", "Not Permitted."

    def get_http_status_code(self) -> HTTPStatus:
        if self.is_USER_NOT_FOUND() or self.is_USER_LOCKING_OUT_WARNING() or self.is_ACCOUNT_SUSPENSION_WARNING() \
                or self.is_CODE_NOT_FOUND() or self.is_NOT_FOUND():
            return HTTPStatus.NOT_FOUND
        elif self.is_USER_LOCKED_OUT() or self.is_ACCOUNT_SUSPENDED() or self.is_AUTH_TOKEN_EXPIRED() \
                or self.is_EXPIRED_OR_INVALID_TOKEN() or self.is_EMAIL_ALREADY_EXISTS() \
                or self.is_FIELDS_ERROR() or self.is_NOT_PERMITTED():
            return HTTPStatus.FORBIDDEN
        elif self.is_AUTH_TOKEN_NOT_FOUND() or self.is_INVALID_AUTH_TOKEN() or self.is_AUTH_FAILED() \
                or self.is_INVALID_REFRESH_TOKEN():
            return HTTPStatus.UNAUTHORIZED
        elif self.value == ErrorCode.INTERNAL_ERROR.value:
            return HTTPStatus.INTERNAL_SERVER_ERROR

        return HTTPStatus.METHOD_NOT_ALLOWED

    def is_same(self, error):
        return self.value == error.value

    def is_ACCOUNT_SUSPENDED(self):
        return self.is_same(ErrorCode.ACCOUNT_SUSPENDED)

    def is_USER_NOT_FOUND(self):
        return self.is_same(ErrorCode.USER_NOT_FOUND)

    def is_USER_LOCKED_OUT(self):
        return self.is_same(ErrorCode.USER_LOCKED_OUT)

    def is_USER_LOCKING_OUT_WARNING(self):
        return self.is_same(ErrorCode.USER_LOCKING_OUT_WARNING)

    def is_ACCOUNT_SUSPENSION_WARNING(self):
        return self.is_same(ErrorCode.ACCOUNT_SUSPENSION_WARNING)

    def is_CODE_NOT_FOUND(self):
        return self.is_same(ErrorCode.CODE_NOT_FOUND)

    def is_EXPIRED_OR_INVALID_TOKEN(self):
        return self.is_same(ErrorCode.EXPIRED_OR_INVALID_TOKEN)

    def is_AUTH_TOKEN_NOT_FOUND(self):
        return self.is_same(ErrorCode.AUTH_TOKEN_NOT_FOUND)

    def is_AUTH_TOKEN_EXPIRED(self):
        return self.is_same(ErrorCode.AUTH_TOKEN_EXPIRED)

    def is_INVALID_AUTH_TOKEN(self):
        return self.is_same(ErrorCode.INVALID_AUTH_TOKEN)

    def is_EMAIL_ALREADY_EXISTS(self):
        return self.is_same(ErrorCode.EMAIL_ALREADY_EXISTS)

    def is_FIELDS_ERROR(self):
        return self.is_same(ErrorCode.FIELDS_ERROR)

    def is_AUTH_FAILED(self):
        return self.is_same(ErrorCode.AUTH_FAILED)

    def is_INVALID_REFRESH_TOKEN(self):
        return self.is_same(ErrorCode.INVALID_REFRESH_TOKEN)

    def is_NOT_PERMITTED(self):
        return self.is_same(ErrorCode.NOT_PERMITTED)

    def is_NOT_FOUND(self):
        return self.is_same(ErrorCode.NOT_FOUND)
