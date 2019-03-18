# coding:utf-8
# Author: K_oul


from flask import Blueprint
from app.api.v1 import record


def create_blueprint_v1():
    bp_v1 = Blueprint('v1', __name__)

    record.api.register(bp_v1)

    return bp_v1

