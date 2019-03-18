from datetime import datetime

from flask import g, jsonify, request

from app.base import db
from app.helpers.api_code import ServerError, Success
from app.helpers.utils import int_id_to_str, preent


def success(api_code=Success, **data):
    """
    :param api_code:
    :param data:
    :return:
    """
    # if api_code.code < 200 or api_code.code > 299:
    #     raise ValueError('success status_code should be 200~299')
    res_data = dict(
        status_code=api_code.code,
        status_message=api_code.msg,
        success=True,
    )
    int_id_to_str(data)
    for k, v in data.items():
        res_data[k] = v
    if g.get('commit_after_resify', None):
        db.session.commit()
    return jsonify(res_data), 200


def error(api_code=ServerError, print_error=True, **data):
    """
    :param api_code:
    :param print_error:
    :param data:
    :return:
    """
    if 200 <= api_code.code <= 299:
        raise ValueError('error status_code can not be 2XX')
    res_data = dict(
        status_code=api_code.code,
        status_message=api_code.msg,
        success=False,
    )
    for k, v in data.items():
        res_data[k] = v
    if print_error:
        preent(datetime.now(), request.path, res_data)
    else:
        res_data['silent_error'] = True
    if g.get('commit_after_resify', None):
        db.session.commit()
    return jsonify(res_data), 200
