from flask import request, abort
import json

from app.helpers.api_code import NoArgError, ArgTypeError
from app.helpers.utils import url_decode

client_errors = (NoArgError, ArgTypeError)


class InvalidArgStatementError(Exception):

    def __init__(self, state):
        self.state = state
        fmt = '[Error] 参数申明错误:"%s",url:"%s"'
        self.message = fmt % (state, request.url)

    def __str__(self):
        return self.message


def _check_arg(state: str, optional: bool, source: dict):
    parts = state.split(':')
    if len(parts) is 0 or len(parts) > 2:
        raise InvalidArgStatementError(state)
    name = parts[0]
    value = source.get(name)
    if value is None or value == '':
        if optional:
            return name, None
        else:
            raise NoArgError(name)
    # print('name:',name,'value:',value)
    if len(parts) is 2:
        type_ = parts[1]
        try:
            if type_ in ('bool', 'boolean'):
                if value not in (True, False):
                    raise ValueError()
                else:
                    return name, value

            elif type_ in ('int', 'integer'):
                return name, int(value)

            elif type_ in ('str', 'string', 'date'):
                if type(value) is not str:
                    raise ValueError()
                return name, value

            elif type_ == 'list':
                if type(value) is str:
                    try:
                        value = json.loads(value)
                    except:
                        raise ValueError()
                if type(value) is not list:
                    raise ValueError()
                return name, value

            elif type_ in ('object', 'obj', 'dict'):
                if type(value) is str:
                    try:
                        value = json.loads(value)
                    except:
                        raise ValueError()
                if type(value) is not dict:
                    raise ValueError()
                return name, value

            else:
                raise InvalidArgStatementError(state)

            # TODO other types

        except ValueError:
            raise ArgTypeError(name, value, type_)
    else:
        return name, value


def check_request_args(*args_state):
    """ Check args from request.args according to given args_state
        return checked data as a dict

        supported state types:
            'foo' : required key
            '?foo' : optional key
            'foo:int' : required key with specific type
            '?foo:int' : optional key with specific type
    """
    args_dict = {}
    for s in args_state:
        if type(s) is not str:
            raise TypeError('参数声明必须是字符串，而非 %s' % s)
        optional = False
        if s.startswith('?'):
            s = s[1:]
            optional = True
        name, arg = _check_arg(s, optional, request.args)
        # 处理python关键字冲突的参数
        # 遇到此类参数会在结尾加下划线传入handler中
        # 此处理仅针对url参数，不影响post body的参数
        if name in ('type', 'for', 'from', 'id'):
            name = name + '_'
        args_dict[name] = arg
    return args_dict


def filter_dict_data(data, args_state=[]):
    """ Filter key and value from given data dict
        transform value type if needed
        and delete keys that not appeared in args_state
        return given data dict

        supported state types:
            'foo' : required key
            '?foo' : optional key
            'foo:int' : required key with specific type
            '?foo:int' : optional key with specific type
    """
    if type(data) is not dict:
        raise NoArgError(None, 'data类型非法')
    valid_keys = []
    err = None
    for s in args_state:
        if type(s) is not str:
            raise TypeError('参数声明必须是字符串, 而非 %s' % s)
        optional = False
        if s.startswith('?'):
            s = s[1:]
            optional = True
        name, value = _check_arg(s, optional, data)
        # print('n:v',name,value)
        if value is not None:
            data[name] = value
            valid_keys.append(name)

    remove_keys = []
    for key in data:
        if key not in valid_keys:
            remove_keys.append(key)

    for key in remove_keys:
        del data[key]

    return data


def check_post_data(args_state):
    """ 从 request.get_json() 中检查指定的参数
        如果失败会抛出 NoArgError 或者 ArgTypeError
    """
    d = request.get_data().decode('utf-8')
    data = {}
    if d:
        try:
            data = json.loads(d)
        except:
            abort(400)
        else:
            if type(data) is not dict:
                raise NoArgError(None, 'body必须是json格式')
            url_decode(data)
    # print(data)
    filter_dict_data(data, args_state)
    return data
