from functools import wraps

from flask import abort

from ..helpers import args_helper


def _make_method_route(blueprint, method, url, check_args=[]):
    """ Make a route decorator that accept specific method
        also checks incoming args
    """
    if type(url) is not str:
        raise ValueError('route url must be string. found %s' % url)

    def decorator(func):

        @blueprint.route(url, methods=[method])
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(check_args) > 0:
                try:
                    checked_args = args_helper.check_request_args(*check_args)

                except args_helper.InvalidArgStatementError as e:
                    print(e.message)
                    return abort(500)

                for k, v in checked_args.items():
                    # print('got arg:',k,v)
                    kwargs[k] = v

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get(blueprint, url, check_args=[]):
    """ @decorator
        define handler for GET method only
    """
    return _make_method_route(blueprint, 'GET', url, check_args)


def post(blueprint, url, check_args=[]):
    """ @decorator
        define handler for POST method only
    """
    return _make_method_route(blueprint, 'POST', url, check_args)
