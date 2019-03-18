# coding:utf-8
# Author: K_oul

from redis import StrictRedis
from json import loads, dumps

from app.config.secure import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_DB


class RedisQueue():
    def __init__(self):
        # 初始化数据库
        self.db = StrictRedis(host=REDIS_HOST, password=REDIS_PASSWORD, port=REDIS_PORT,
                              db=REDIS_DB, decode_responses=True)

    def add(self, key, data):
        # print('添加{}成功'.format(key))
        return self.db.rpush(key, dumps(data))

    def pop(self, key):
        if self.db.llen(key):
            return loads(self.db.lpop(key))
        return False

    def empty(self, key):
        return self.db.llen(key) == 0

