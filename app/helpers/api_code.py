class NoArgError(Exception):

    def __init__(self, name, message=None):
        if message:
            self.name = None
            self.message = message
        else:
            self.name = name
            self.message = '缺少参数"%s"' % name


class ArgTypeError(Exception):

    def __init__(self, name, value, required_type):
        self.name = name
        self.value = value
        self.required_type = required_type
        fmt = '参数"%s"的类型必须是"%s",而非"%s"'
        self.message = fmt % (name, required_type, value)


class ApiCodeBase:
    code = 0
    msg = '成功'


class Success(ApiCodeBase):
    code = 200
    msg = '成功'


class TestApiCode(ApiCodeBase):
    code = -1200
    msg = '请求失败：因为这是一个测试API'


class SeverMaintained(ApiCodeBase):
    code = 12000
    msg = '服务器维护中'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[Error] %s' % msg)


class ApiLocked(ApiCodeBase):
    code = 12001
    msg = '当前功能被锁定，请稍后再试'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[Error] %s' % msg)


class TaskWaitTimeout(ApiCodeBase):
    code = 12002
    msg = '服务器繁忙，请稍后重试'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[Error] %s' % msg)


class LocalAPIForbidden(ApiCodeBase):
    code = 12003
    msg = '当前行为在本地被禁用'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[Error] %s' % msg)


class AuthFailed(ApiCodeBase):
    code = 403
    msg = '认证失败'


class NotFound(ApiCodeBase):
    code = 404
    msg = 'Not Found'


class MethodNotAllowed(ApiCodeBase):
    code = 405
    msg = 'Method Not Allowed'


class InvalidArgument(ApiCodeBase):
    code = 400
    msg = '参数错误'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[参数错误] %s' % msg)


class ServerError(ApiCodeBase):
    code = 500
    msg = '服务器错误'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print('[服务器错误] %s' % msg)


class SqlDataError(ApiCodeBase):
    code = 4000
    msg = '输入数据不合法，请检查是否有非法输入 \
    (比如数字/文字超长，或者在应该输入数字的地方输入了文字等）'


class ResourceNotFound(ApiCodeBase):
    code = 4004
    msg = '资源不存在'

    def __init__(self, msg: str):
        self.msg += ':%s' % msg
        print('[资源不存在] %s' % msg)


class ResourceAlreadyCreated(ApiCodeBase):
    code = 4005
    msg = '资源已存在'

    def __init__(self, msg: str):
        self.msg += ':%s' % msg
        print('[资源已存在] %s' % msg)


class WxAuthError(ApiCodeBase):
    code = 4009
    msg = '微信认证失败'


class ArgTypeApiCode(ApiCodeBase):
    """
    需要实例化使用
    """
    code = 10041
    msg = ''

    def __init__(self, e: ArgTypeError):
        self.msg = e.message


class NoArgApiCode(ApiCodeBase):
    """
    需要实例化使用
    """
    code = 10042
    msg = ''

    def __init__(self, e: NoArgError):
        self.msg = e.message


class UserTokenNotFound(ApiCodeBase):
    code = 10031
    msg = '找不到用户凭据'


class UserTokenIllegal(ApiCodeBase):
    code = 10032
    msg = '用户凭据不合法'


class UploadTemporaryImageFailed(ApiCodeBase):
    code = 110001
    msg = '上传临时图片失败'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print(self.msg)


class DecryptWxDataFailed(ApiCodeBase):
    code = 110002
    msg = '微信授权失败'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print(self.msg)


class UserNotFollowMp(ApiCodeBase):
    code = 110003
    msg = '用户未关注'

    def __init__(self, msg=None):
        self.msg += ':%s' % msg
        print(self.msg)
