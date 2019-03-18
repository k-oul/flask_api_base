# coding:utf-8
# Author: K_oul

import time


def today_time():
    now_time = int(time.time())
    day_time = now_time - now_time % 86400 + time.timezone
    return day_time
