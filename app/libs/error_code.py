# coding:utf-8
# Author: K_oul


from app.libs.error import APIException


class SuccessData(APIException):
    code = 200
    status_message = 'ok'
    status_code = 200


class Success(APIException):
    code = 201
    status_message = 'ok'
    status_code = 200


class ServerError(APIException):
    code = 500
    status_message = 'Sorry, we made a mistake!'
    status_code = 500


class ClientTypeError(APIException):
    code = 400
    status_message = 'client is invalid'
    status_code = 1006


class ParameterException(APIException):
    code = 400
    status_message = 'invalid parameter'
    status_code = 1000


class NotFound(APIException):
    code = 404
    status_message = 'the resoure are not found !'
    status_code = 404


class AuthFailed(APIException):
    code = 401
    status_code = 401
    status_message = 'authorization failed'

