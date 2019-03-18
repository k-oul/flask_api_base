from app.helpers.api_code import ServerError


class CommonException(Exception):

    def __init__(self, api_base=ServerError):
        if not api_base:
            api_base = ServerError
        self.code = api_base.code
        self.message = api_base.msg
        self.api_base = api_base


class CeleryTaskException(Exception):

    def __init__(self, api_base=ServerError):
        if not api_base:
            api_base = ServerError
        self.code = api_base.code
        self.message = api_base.msg
        self.api_base = api_base
