# from app.base import run_env# ENV_DEV, ENV_PROD, ENV_LOCAL
import json
import time
from time import sleep
import hashlib
import random

import requests
from flask import session, redirect, url_for

from app.base import redis
from app.helpers import utils  # , xml_helper
from app.helpers.api_code import UserNotFollowMp
from app.helpers.exceptions import CommonException

WXA_SERVER_ACCESS_TOKEN_HASH = 'mp_server_access_token'
WXA_SERVER_ACCESS_TOKEN_HASH_LOCK = 'lock:mp_server_access_token'

WXA_JS_TICKET_HASH = 'mp_js_ticket'
WXA_JS_TICKET_HASH_LOCK = 'lock:mp_js_ticket'

wxweb_js_ticket_hash = "wxweb_js_ticket"
wxweb_js_ticket_hash_lock = "lock:wxweb_js_ticket"

from app.configs.config import mp_appid
from app.configs.config import mp_secret
from app.configs.config import other_mp

appid = mp_appid
secret = mp_secret

TOKEN_EXPIRE = 5400

WEIXIN_ERROR_EXPLAIN = {
    '-1': '系统繁忙',
    '40001': '获取access_token时AppSecret错误，或者access_token无效',
    '40004': '不合法的媒体文件类型',
    '40005': '不合法的文件类型',
    '40006': '不合法的文件大小',
    '40007': '不合法的媒体文件id',
    '40008': '不合法的消息类型',
    '40009': '不合法的图片文件大小',
    '40010': '不合法的语音文件大小',
    '40011': '不合法的视频文件大小',
    '45008': '图文消息超过限制',
    '45009': '接口调用超过限制',
    '48001': 'api功能未授权，请确认公众号已获得该接口，可以在公众平台官网-开发者中心页中查看接口权限',
    '48004': 'api接口被封禁，请登录mp.weixin.qq.com查看详情',
    '50001': '用户未授权该api',
    '50002': '用户受限，可能是违规后接口被封禁',
    '61023': 'refresh token失效，请重新授权'
}


class WeixinRequestError(Exception):
    def __init__(self, status_code, message=''):
        self.status_code = status_code
        if WEIXIN_ERROR_EXPLAIN.get(str(status_code)):
            message = WEIXIN_ERROR_EXPLAIN.get(str(status_code))
        self.message = json.dumps(message, ensure_ascii=False)
        self.wx_response = message


def get_wx_web_oauth_access_token(code):
    """
    获取网页登录的access token， 每个用户唯一
    :param code:
    :return:
    """
    # 没有上锁
    url = utils.gen_url(
        'https://api.weixin.qq.com/sns/oauth2/access_token',
        appid=appid,
        secret=secret,
        code=code,
        grant_type='authorization_code'
    )
    r = requests.get(url, timeout=5)

    # { "access_token":"ACCESS_TOKEN",
    #   "expires_in":7200,
    #   "refresh_token":"REFRESH_TOKEN",
    #   "openid":"OPENID",
    #   "scope":"SCOPE" }

    if r.status_code != 200:
        raise WeixinRequestError(
            r.status_code, 'http_status_code: %s' % r.status_code)
    data = r.json()
    if data.get('errcode'):
        raise WeixinRequestError(data.get('errcode'), data)

    token = data.get('access_token')
    openid = data.get('openid')

    return token, openid


def get_mp_access_token():
    """
    获取公众号的Access Token
    :return:
    """
    token = redis.get(WXA_SERVER_ACCESS_TOKEN_HASH)
    if token:
        return token
    h = WXA_SERVER_ACCESS_TOKEN_HASH_LOCK
    lock_count = redis.incrby(h, 1)
    if lock_count == 1:
        redis.expire(h, 10)
        # 没有上锁
        url = utils.gen_url(
            'https://api.weixin.qq.com/cgi-bin/token',
            grant_type='client_credential',
            appid=appid,
            secret=secret
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            redis.delete(h)
            raise WeixinRequestError(
                r.status_code, 'http_status_code: %s' % r.status_code)
        data = r.json()
        if data.get('errcode'):
            redis.delete(h)
            raise WeixinRequestError(data.get('errcode'), data)
        token = data.get('access_token')
        redis.set(WXA_SERVER_ACCESS_TOKEN_HASH, token)
        redis.expire(WXA_SERVER_ACCESS_TOKEN_HASH, TOKEN_EXPIRE)
        redis.delete(h)
        return token
    else:
        if lock_count > 30:
            redis.delete(h)
            raise WeixinRequestError('-1', 'http_status_code:%s' % '-1')
        # 已经有别人上锁了
        sleep(1)
        return get_mp_access_token()

def get_user_info_by_web(web_token,openid):
    url = utils.gen_url(
        "https://api.weixin.qq.com/sns/userinfo",
        access_token = web_token,
        openid = openid,
        lang = "zh_CN"
    )
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        raise WeixinRequestError(
            r.status_code, 'http_status_code: %s' % r.status_code)
    r.encoding = "utf8mb4"
    data = r.json()
    if data.get('errcode'):
        raise WeixinRequestError(data.get('errcode'), data)

    return data

def get_user_info(mp_token, openid):
    url = utils.gen_url(
        'https://api.weixin.qq.com/cgi-bin/user/info',
        access_token=mp_token,
        openid=openid,
        lang='zh_CN',
    )
    r = requests.get(url, timeout=5)
    # {
    #     "subscribe": 1,
    #     "openid": "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",
    #     "nickname": "Band",
    #     "sex": 1,
    #     "language": "zh_CN",
    #     "city": "广州",
    #     "province": "广东",
    #     "country": "中国",
    #     "headimgurl":"http://thirdwx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/0",
    #     "subscribe_time": 1382694957,
    #     "unionid": " o6_bmasdasdsad6_2sgVt7hMZOPfL"
    #                "remark": "",
    # "groupid": 0,
    # "tagid_list":[128,2],
    # "subscribe_scene": "ADD_SCENE_QR_CODE",
    # "qr_scene": 98765,
    # "qr_scene_str": ""
    # }
    if r.status_code != 200:
        raise WeixinRequestError(
            r.status_code, 'http_status_code: %s' % r.status_code)
    data = r.json()
    if data.get('errcode'):
        raise WeixinRequestError(data.get('errcode'), data)

    # if int(data.get('subscribe')) == 0:
    #     raise CommonException(UserNotFollowMp)

    return data

def get_wxweb_client_js_ticket():
    ticket = redis.get(wxweb_js_ticket_hash)
    if ticket:
        return ticket
    h = wxweb_js_ticket_hash_lock
    lock_count = redis.incrby(h,1)
    print(lock_count)
    if lock_count == 1:
        redis.expire(h,10)
        token = get_mp_access_token()
        url = utils.gen_url(
            "https://api.weixin.qq.com/cgi-bin/ticket/getticket",
            access_token = token,
            type = "jsapi"
        )
        r = requests.get(url,timeout=5)
        if r.status_code != 200:
            redis.delete(h)
            raise WeixinRequestError(r.status_code,r.json())
        data = r.json()
        if data.get("errcode"):
            redis.delete(h)
            raise WeixinRequestError(data.get("errcode"),r.json())
        ticket = data.get("ticket")
        redis.set(wxweb_js_ticket_hash, ticket)
        redis.expire(wxweb_js_ticket_hash, TOKEN_EXPIRE)
        redis.delete(h)
        return ticket
    # elif lock_count >= 20:
    #     redis.delete(h)
    #     return get_wxweb_client_js_ticket()
    else:
        sleep(1)
        return get_wxweb_client_js_ticket()

def signature_js_api(url):
    nonce_str = str(random.randint(1, 10000000000000))
    time_stamp = str(int(time.time()))
    js_ticket = get_wxweb_client_js_ticket()
    d = [
        "jsapi_ticket=" + js_ticket,
        "noncestr=" + nonce_str,
        'timestamp=' + time_stamp,
        'url=' + utils.quote_url_args(url)
    ]
    # print(d)
    s = "&".join(d)
    # print(s)
    m = hashlib.sha1()
    m.update(str.encode(s))
    sign = m.hexdigest()
    # print(sign)
    return dict(
        nonce_str=nonce_str,
        time_stamp=time_stamp,
        url=url,
        s=s,
        sign=sign,
    )

def redirect_get_base_code(handler, generate_url_only=False):
    target_url = url_for(handler, _external=True)
    print(target_url)
    url = utils.gen_url(
        "https://open.weixin.qq.com/connect/oauth2/authorize",
        ("appid", mp_appid),
        ("redirect_uri", target_url),
        ("response_type", "code"),
        ("scope", "snsapi_base"),
        ("state", "STATE")
    ) + "#wechat_redirect"
    if generate_url_only:
        return url
    else:
        return redirect(url)

def get_other_mp_access_token(mp):
    token_hash = "%s:access_token"%mp["appid"]
    lock_hash = "%s:access_token_lock"%mp["appid"]
    token = redis.get(token_hash)
    if token:
        return token
    lock_count = redis.incrby(lock_hash, 1)
    if lock_count == 1:
        redis.expire(lock_hash, 10)
        # 没有上锁
        url = utils.gen_url(
            'https://api.weixin.qq.com/cgi-bin/token',
            grant_type='client_credential',
            appid=mp["appid"],
            secret=mp["secret"]
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            redis.delete(lock_hash)
            raise WeixinRequestError(
                r.status_code, 'http_status_code: %s' % r.status_code)
        data = r.json()
        if data.get('errcode'):
            redis.delete(lock_hash)
            raise WeixinRequestError(data.get('errcode'), data)
        token = data.get('access_token')
        redis.set(token_hash, token, ex=TOKEN_EXPIRE)
        redis.delete(lock_hash)
        return token
    else:
        if lock_count > 30:
            redis.delete(lock_hash)
            raise WeixinRequestError('-1', 'http_status_code:%s' % '-1')
        # 已经有别人上锁了
        sleep(1)
        return get_other_mp_access_token(mp)

def get_mp_auto_reply(mp):
    url = utils.gen_url(
        "https://api.weixin.qq.com/cgi-bin/get_current_autoreply_info",
        access_token = get_other_mp_access_token(mp),
    )
    r = requests.get(url,timeout=5)
    data = r.json()
    print(data)
    return data

def post_text(mp,openid,text):
    url = utils.gen_url(
        "https://api.weixin.qq.com/cgi-bin/message/custom/send",
        access_token = get_other_mp_access_token(mp),
    )
    body = dict(
        touser = openid,
        msgtype = "text",
        text = dict(
            content = text
        )
    )
    data = json.dumps(body,ensure_ascii=False).encode('utf8')
    r = requests.post(url,data=data,timeout=5)
    data = r.json()
    return True

def get_mp_menu(mp):
    url = utils.gen_url(
        "https://api.weixin.qq.com/cgi-bin/menu/get",
        access_token = get_other_mp_access_token(mp),
    )
    r = requests.get(url,timeout=5)
    data = r.json()
    return data

def get_user_list(mp,next_openid=None,count=None):
    if next_openid:
        url = utils.gen_url(
            "https://api.weixin.qq.com/cgi-bin/user/get",
            access_token = get_other_mp_access_token(mp),
            next_openid = next_openid,
            count = count,
        )
    else:
        url = utils.gen_url(
            "https://api.weixin.qq.com/cgi-bin/user/get",
            access_token = get_other_mp_access_token(mp),
            count = count,
        )
    r = requests.get(url,timeout=10)
    data = r.json()
    user_list = data.get("data").get("openid")
    count = data.get("count")
    next_openid = data.get("next_openid")
    return [count,next_openid,user_list]

def get_user_list_info(mp,openid_list):
    user_info_url = utils.gen_url(
        "https://api.weixin.qq.com/cgi-bin/user/info/batchget",
        access_token = get_other_mp_access_token(mp),
    )
    if type(openid_list[0]) == str:
        openid_list = [dict(openid=x,lang="zh_CN") for x in openid_list]
    r = requests.post(user_info_url,json={"user_list":openid_list},timeout=5)
    r.encoding = "utf8mb4"
    try:
        data = json.loads(r.text,strict=False)
    except Exception:
        print("解析用户信息失败!!!")
        print(r.text)
        return []
    return data["user_info_list"]
