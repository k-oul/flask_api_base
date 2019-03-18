import datetime
import json

from app.base import redis
from app.helpers.utils import debug
from app.models.user import User

EXPIRE_TIME_LONG = 7 * 24 * 3600
EXPIRE_TIME_NORMAL = 24 * 3600
EXPIRE_TIME_SHORT = 2 * 3600


def model_to_cache(model, cache_keys=None):
    # d = model.get_attr_dict()
    if cache_keys is None:
        cache_keys = []
    return dict_to_cache(model.to_dict(ignore_hash_id_map=True), cache_keys)


def dict_to_cache(d: dict, cache_keys=None):
    # d = model.get_attr_dict()
    if cache_keys is None:
        cache_keys = []
    cache_data = {}
    for key in cache_keys:
        cache_data[key] = d[key]
        if type(cache_data[key]) is datetime.datetime:
            cache_data[key] = cache_data[key].timestamp()
        if type(cache_data[key]) is datetime.date:
            _datetime = datetime.datetime.combine(
                cache_data[key], datetime.datetime.min.time())
            cache_data[key] = _datetime.timestamp()
    return cache_data


def get_user_cache(token, album_id=None):
    if not album_id:
        cache_hash = 'user:%s' % token
    else:
        cache_hash = 'user:%s:%s' % (token, album_id)
    return redis.get(cache_hash)


def update_user_cache(user):
    if not user:
        return None

    cache_hash = 'user:%s' % user.token
    cache_data = model_to_cache(user, User.cache_keys)

    redis.set(cache_hash, json.dumps(cache_data))
    redis.expire(cache_hash, EXPIRE_TIME_NORMAL)
    return cache_data


def clear_user_cache(user_token: str):
    """
    清除用户数据缓存
    :param user_token:
    :param album_id:
    :return:
    """
    debug('clear user cache [ User Token ] ', user_token)
    if not user_token:
        return None

    cache_hash = 'user:%s' % user_token
    redis.delete(cache_hash)
