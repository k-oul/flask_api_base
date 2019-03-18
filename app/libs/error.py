# coding:utf-8
# Author: K_oul


from flask import request, json
from werkzeug.exceptions import HTTPException


class APIException(HTTPException):
    code = 200
    status_message = 'sorry, we make a mistake!'
    status_code = 999
    success = True
    data = ''

    def __init__(self, status_message=None, code=None, status_code=None, data=None, success=None):
        if code:
            self.code = code
        if status_message:
            self.status_message = status_message
        if status_code:
            self.status_code = status_code
        if data:
            self.data = data
        if success:
            self.success = success
        super().__init__(status_message, None)

    def get_body(self, environ=None):
        body = dict(
            status_message=self.status_message,
            status_code=self.status_code,
            success=self.success,
            data=self.data,
            request=request.method + ' ' + self.get_url_no_parm(),
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]

    @staticmethod
    def get_url_no_parm():
        full_path = str(request.full_path)
        main_path = full_path.split('?')
        return main_path[0]
