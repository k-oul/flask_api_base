# coding:utf-8
# Author: K_oul

import requests
from random import shuffle

from app import redis_queue
from app.config.secure import POOL_KEY


class HTTP:
    @staticmethod
    def get(url, **kwargs):

        r = requests.get(url=url, **kwargs)
        r.encoding = r.apparent_encoding
        if r.status_code != 200:
            return
        else:
            return r

    @staticmethod
    def post(url, **kwargs):
        r = requests.post(url=url, **kwargs)
        r.encoding = r.apparent_encoding
        if r.status_code != 200:
            return
        else:
            return r

    @staticmethod
    def get_proxy(get_proxy_api=None):
        if redis_queue.db.hlen(POOL_KEY) >= 10:
            ps = redis_queue.db.hkeys(POOL_KEY)
            shuffle(ps)
            redis_queue.db.hincrby(POOL_KEY, ps[0], 1)
            return ps[0]

        r = requests.get(get_proxy_api)
        r_data = r.json()
        proxy_list = r_data["data"]["proxy_list"]
        for p in proxy_list:
            redis_queue.db.hset(POOL_KEY, p, 1)


    @staticmethod
    def del_proxy(proxy):
        redis_queue.db.hdel(POOL_KEY, proxy)




