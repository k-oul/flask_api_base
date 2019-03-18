""" helpers 中的内容都不需要在app启动时加载, 由他们的使用者自行import
    如果 helper 的本体是一个class, 那么这个class不应该在module内被实例化, 而是应该被它的使用者实例化
"""

import binascii
import datetime
import hashlib
import json
import random
import re
import time
from urllib.parse import unquote

import requests
from flask import g

from app.configs.config import DEBUG, user_password_salt
from app.helpers.api_code import UploadTemporaryImageFailed
from app.helpers.exceptions import CommonException


class DictWrapper:
    """ Wraps a dict into an instance of DictWrapper
        key and value in this dict can be get more easieer.

        example:
            d = dict(key='value')

            d['key'] == DictWrapper(d).key == 'value'

            d['not_exist_key'] -> got a KeyError
            DictWrapper(d).not_exist_key -> None(non-strict) | KeyError(strict)
    """

    def __init__(self, data: dict = {}, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.__dict = data

    def get_dict_(self):
        return self.__dict

    def get_(self, key):
        """ 允许空值的取值方式 """
        return self.__dict.get(key)

    def delete_(self, key):
        if key in self.__dict:
            del self.__dict[key]
            return True
        else:
            return False

    def __check(self, name):
        if self.strict_mode and name not in self.__dict:
            msg = 'Can not find key "%s" in "%s"' % (name, self)
            raise KeyError(msg)

    def __getattr__(self, name):
        # for attr access like 'wrapper.name'
        self.__check(name)
        return self.__dict.get(name)

    def __getitem__(self, key):
        # for index access like 'wrapper['key']'
        self.__check(key)
        return self.__dict.get(key)

    def __iter__(self):
        for key in self.__dict:
            yield (key)

    def keys(self):
        return self.__dict.keys()

    def __str__(self):
        return 'DictWrapper(%s)' % str(self.__dict)

    def to_dict(self):
        return self.__dict

    __repl__ = __str__


def gen_hash_id():
    """ Generate a hash id by date and random number
    """
    t = time.time()
    # 1296 = 36^2, 46655 = 36^3 - 1
    s = base36_encode(int(t))
    s += base36_encode(int(random.randint(1296, 46655)))
    # print(s)
    return s


def gen_num_hash_id(redis, key='common'):
    t = time.time()
    s = str(int(t))[1:]
    i = redis.incr('unique-randint:%s:%s' %
                   (key, s), random.randint(1, 30)) + 1320
    redis.expire('unique-randint:%s:%s' % (key, s), 5)
    s = s + str(i)
    return (str(int(s) - 3814463512124))


def gen_user_token():
    """ Generate a user token by hash_id and md5
    """
    salt1 = '90cjg3kn'
    salt2 = '10vngk39c'
    hash_id = gen_hash_id()
    md5_str = hashlib.md5((hash_id + salt1).encode('utf8')).hexdigest()
    sha_str = hashlib.sha256((hash_id + salt2).encode('utf8')).hexdigest()
    s = md5_str[8:32] + sha_str[2:7] + md5_str[:8] + sha_str[12:15]
    return s


def base36_encode(number):
    if not isinstance(number, int):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')

    alphabet, base36 = ['0123456789abcdefghijklmnopqrstuvwxyz', '']

    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36 or alphabet[0]


def gen_url(url, *ordered_url_args: '((key,value))', **url_args):
    args = []
    for t in ordered_url_args:
        (k, v) = t
        if v is not None:
            args.append('%s=%s' % (k, requests.utils.quote(str(v))))
    for k, v in url_args.items():
        if v is not None:
            args.append('%s=%s' % (k, requests.utils.quote(str(v))))
    if args:
        url = '%s?%s' % (url, '&'.join(args))
    # print('gen url', url)
    return url


def base36_decode(number):
    return int(number, 36)


def filter_dict(old_dict, keys):
    for key in old_dict.keys():
        if key not in keys:
            old_dict.pop(key)
    return old_dict


def currency(value):
    """ 将分为单位的价格转换为元为单位
    """
    if not value and value != 0:
        return ''
    if value % 100 == 0:
        return int(value / 100)
    else:
        return value / 100


def summary(text, length=10, ellipsis=True):
    if len(text) < length:
        return text
    else:
        s = text[:length]
        if ellipsis:
            s = s + '…'
        return s


def time_from_now(value):
    if not value:
        return ''
    then = datetime.datetime.fromtimestamp(value)
    now = datetime.datetime.now()
    # print('now:',now,'then:',then)
    delta = now - then
    if delta > datetime.timedelta(days=364):
        return then.strftime('%Y-%m-%d %H:%M')
    elif delta > datetime.timedelta(days=2):
        return then.strftime('%m月%d日 %H:%M')
    elif delta > datetime.timedelta(days=1):
        return '昨天 %s' % then.strftime('%H:%M')
    elif delta > datetime.timedelta(hours=1):
        return '%s小时前' % int(delta.seconds / 3600)
    elif delta > datetime.timedelta(minutes=1):
        return '%s分钟前' % int(delta.seconds / 60)
    else:
        return '刚刚'


def hash_to_hex(hash_str):
    hex_str = binascii.hexlify(hash_str.encode('ascii'))
    return hex_str.upper().decode('ascii')


def hex_to_hash(hex_str):
    return binascii.unhexlify(hex_str).decode('ascii')


def r(url):
    num = random.randint(0, 99999)
    if url.find('?') > -1:
        return url + '&r=%d' % num
    else:
        return url + '?r=%d' % num


def set_cookie(name, value, **kwargs):
    if not hasattr(g, 'set_cookies'):
        g.set_cookies = []
    g.set_cookies.append((name, value, kwargs))


def get_random_color():
    colors = [
        '#006699', '#009966', '#009999',
        '#663399', '#6666ff', '#66cc66',
        '#993366', '#ff6666', '#ff9933',
        '#ffcc33', '#ffff66', '#cccc99',
        '#99cc66'
    ]
    return colors[random.randint(0, len(colors) - 1)]


def encrypt_password(password):
    password = hashlib.sha256(
        (password + user_password_salt).encode('utf8')).hexdigest()
    return password


def seconds_to_tomorrow():
    now = datetime.datetime.now()
    return (86400 - (now.hour * 3600 + now.minute * 60 + now.second))


def underlize(obj):
    if not obj:
        return None
    else:
        out = {}
        for k in obj.keys():
            v = obj[k]
            out[underlize_key(k)] = v
        return out


def underlize_key(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def camelize(obj):
    if not obj:
        return None
    else:
        out = {}
        for k in obj.keys():
            v = obj[k]
            out[camelize_key(k)] = v
        return out


def camelize_key(name):
    out = []
    i = 0
    while i < len(name):
        if name[i] in ['-', '_']:
            out.append(name[i + 1].upper())
            i += 1
        else:
            out.append(name[i])
        i += 1
    return ''.join(out)


def gen_random_token():
    return base36_encode(int(random.randint(12960000000000, 466550000000000)))


def replace_dict_value(data, pattern, value):
    for k in data.keys():
        if type(data[k]) == str:
            data[k] = data[k].replace(pattern, value)
        elif type(data[k]) == dict:
            data[k] = replace_dict_value(data[k], pattern, value)
    return data


def string_to_list(string: str, token=','):
    """ 将字符串转换为一个列表
    """
    if not string:
        return []
    if string == '[]':
        return []
    return string.split(token)


def list_to_string(list_: list, token=','):
    """ 将列表转为一串字符
        eg. token(*) : [1, 2, 3, 4, 5] => 1*2*3*4*5
    """
    if not list_:
        return None

    if len(list_) == 1:
        return '%s,' % token.join(map(str, list_))

    return token.join(map(str, list_))


def debug(*args):
    """
    在测试环境下打印内容
    :param args:
    :return:
    """
    if DEBUG:
        print('\033[96m[DEBUG]\033[00m', end='')
        for i in range(len(args)):
            print('\033[93m {}\033[00m'.format(args[i]), end='')
        print('')


def get_lunar_month_str_by_int(month_int):
    lunar_months = ['',
                    '正月',
                    '二月',
                    '三月',
                    '四月',
                    '五月',
                    '六月',
                    '七月',
                    '八月',
                    '九月',
                    '十月',
                    '十一月',
                    '腊月']
    return lunar_months[month_int]


def get_lunar_day_str_by_int(day_int):
    lunar_day = ['',
                 '一',
                 '二',
                 '三',
                 '四',
                 '五',
                 '六',
                 '七',
                 '八',
                 '九',
                 '十']

    if day_int <= 0:
        day_int = 1
    if day_int > 31:
        day_int = 31

    if 1 <= day_int <= 10:
        return '初%s' % lunar_day[day_int]

    if 11 <= day_int <= 19:
        return '%s%s' % (lunar_day[10], lunar_day[day_int - 10])

    if 20 <= day_int <= 29:
        return '%s%s%s' % (lunar_day[2], lunar_day[10], lunar_day[day_int - 20])

    if 30 <= day_int <= 31:
        return '%s%s%s' % (lunar_day[3], lunar_day[10], lunar_day[day_int - 30])


def get_lunar_str_by_time(tm):
    """
    通过 时间戳（int） 或者datetime对象，获取农历月日出生时间
    :param tm:
    :return:
    """
    if isinstance(tm, datetime.datetime):
        dt = tm
    else:
        dt = datetime.datetime.fromtimestamp(tm)
    from LunarSolarConverter.LunarSolarConverter import Solar, LunarSolarConverter
    solar = Solar(dt.year, dt.month, dt.day)
    lunar = LunarSolarConverter().SolarToLunar(solar)

    month_str = get_lunar_month_str_by_int(lunar.lunarMonth)
    day_str = get_lunar_day_str_by_int(lunar.lunarDay)

    return '农历%s%s' % (month_str, day_str)


def get_constellation(month: int, day: int):
    """
    通过月份和日期,获取中文的星座描述
    :param month:
    :param day:
    :return:
    """
    dates = (21, 20, 21, 21, 22, 22, 23, 24, 24, 24, 23, 22)
    constellations = ('摩羯',
                      '水瓶',
                      '双鱼',
                      '白羊',
                      '金牛',
                      '双子',
                      '巨蟹',
                      '狮子',
                      '处女',
                      '天秤',
                      '天蝎',
                      '射手',
                      '摩羯')
    if day < dates[month - 1]:
        return '%s座' % constellations[month - 1]
    else:
        return '%s座' % constellations[month]


def get_age_by_time(tm, now=datetime.datetime.now()):
    """
    传入 一个时间(datetime) 或 时间戳(int),
    获取该时间到某个时间(默认为现在)的时间差描述
    :param tm:
    :param now:
    :return:
    """
    if isinstance(tm, datetime.datetime):
        birth_datetime = tm
    else:
        birth_datetime = datetime.datetime.fromtimestamp(tm)

    days = (now - birth_datetime).days
    if days < 0:
        return '暂未出生'
    if days == 0:
        return '刚刚出生'

    year = int(days / 365)
    month = int(days % 365 / 30)

    if year == 0 and month == 0:
        return '%s天' % days

    if year == 0 and month != 0:
        return '%s个月' % month

    return '%s岁' % year if not month \
        else '%s岁%s个月' % (year, month)


def int_id_to_str(data: dict):
    """
    将dict中的所有key为(包含)id字段的int转换为str,
    结构中超过10个长度int,也将被转换为str
    :param data:
    :return:
    """
    for k, v in data.items():

        if isinstance(v, dict):
            int_id_to_str(v)
            continue

        if isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    int_id_to_str(item)
                    continue
                if isinstance(item, int):
                    if len(str(item)) > 10:
                        v[i] = str(item)

        if isinstance(k, str) \
                and k.find('id') >= 0 \
                and isinstance(v, int):
            data[k] = str(v)
            continue

        if isinstance(v, int) \
                and len(str(v)) > 10:
            data[k] = str(v)
            continue


def preent(*data):
    """
    print in green color
    :param data:
    :return:
    """
    for i in range(len(data)):
        print('\033[91m{}\033[00m'.format(data[i]), end='')
    print('')


def get_last_active_str_by_time(tm):
    if not tm:
        return None

    if isinstance(tm, datetime.datetime):
        tm = time.mktime(tm.timetuple())

    now = time.time()
    seconds = int(now - tm)
    if seconds <= 0:
        return '刚刚'

    debug(seconds)

    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7
    month = day * 30
    year = day * 365

    if 0 < seconds < minute:
        return '%s秒前' % seconds
    if minute <= seconds < hour:
        return '%s分钟前' % int(seconds / minute)
    if hour <= seconds < day:
        return '%s小时前' % int(seconds / hour)
    if day <= seconds < week:
        return '%s天前' % int(seconds / day)
    if week <= seconds < month:
        return '%s周前' % int(seconds / week)
    if month <= seconds < year:
        return '%s个月前' % int(seconds / month)
    if year <= seconds:
        return '%s年前' % int(seconds / year)


def update_value_cache_list(redis, key, filed, value, type_='append'):
    if not key or not filed or not value:
        return None

    list_ = redis.hget(key, filed)
    if not list_:
        list_ = '[]'
    list_ = json.loads(list_)

    if type_ == 'append':
        if value in list_:
            return None
        list_.append(value)
    elif type_ == 'del':
        if value in list_:
            del list_[list_.index(value)]
        else:
            return None

    redis.hset(key, filed, json.dumps(list_))


def url_decode(data: dict):
    """
    decode url params
    :param data:
    :return:
    """
    for key in data:
        value = data[key]
        if isinstance(value, dict):
            url_decode(value)
            continue
        if isinstance(value, str):
            data[key] = unquote(data[key], 'utf-8')


def cast_dict_items_to_str(data: dict):
    """
    :param data:
    :return:
    """
    for key in data:
        value = data[key]

        if isinstance(key, int):
            old_key = key
            key = str(old_key)
            data[key] = data[old_key]
            data.pop(old_key, None)

        if isinstance(value, dict):
            cast_dict_items_to_str(value)
            continue

        if isinstance(value, list):
            for i, li in enumerate(value):
                if isinstance(li, int):
                    value[i] = str(li)
            continue

        if isinstance(value, int):
            data[key] = str(value)


def get_parent_desc_in_chinese(parent):
    """
    :param parent:
    :return:
    """
    if parent == 'mother':
        return '妈妈'
    if parent == 'father':
        return '爸爸'
    return None


def quote_url_args(url):
    parts = url.split('?')
    if len(parts) > 1:
        args = parts[-1].split('&')
        for i, a in enumerate(args):
            kAndV = a.split('=')
            if len(kAndV) > 1:
                kAndV[1] = requests.utils.quote(kAndV[1])
                args[i] = ('='.join(kAndV))
        parts[-1] = '&'.join(args)
    return '?'.join(parts)


def get_media_id_from_temporary_img(aceess_token, local_img_path):
    """
    上传一张临时图片到微信伺服器
    返回一个微信服务器可识别的media id
    3天后失效
    :param aceess_token:
    :param local_img_path:
    :return:
    """

    url = 'https://api.weixin.qq.com/cgi-bin/media/upload?access_token=%s&type=image' \
          % aceess_token
    files = {'media': open(local_img_path, 'rb')}
    rs = None
    try:
        rs = requests.post(url, files=files)
        media_id = rs.json().get('media_id')
        if not media_id:
            raise CommonException(UploadTemporaryImageFailed(rs.text))
        return media_id
    except Exception as e:
        import traceback
        traceback.print_tb(e.__traceback__)
        if rs:
            preent(rs.text)
        raise CommonException(UploadTemporaryImageFailed)
