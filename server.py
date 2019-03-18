# coding:utf-8
# Author: K_oul


from app import create_app
from werkzeug.exceptions import HTTPException

from app.libs.error import APIException
from app.libs.error_code import ServerError

app = create_app()


@app.errorhandler(Exception)
def framework_error(e):
    if isinstance(e, APIException):
        return e
    if isinstance(e, HTTPException):
        code = e.code
        status_message = e.description
        error_code = 1007
        return APIException(status_message, code, error_code)
    else:
        # 调试模式
        # log
        if not app.config['DEBUG']:
            return ServerError()
        else:
            raise e


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

