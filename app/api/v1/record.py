# coding:utf-8
# Author: K_oul

from flask import request

from app.libs.error_code import SuccessData, ParameterException, Success
from app.libs.redprint import Redprint
from app.libs.utils import today_time

api = Redprint('record')

@api.route('/query', methods=['GET'])
def query():
    args = request.args
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    status = args.get('status')
    job_name = args.get('job_name')
    mp_name = args.get('mp_name')
    limit = args.get('limit')
    offset = args.get('offset')
    try:
        data = get_commment_info(start_date, end_date, status, job_name, mp_name, limit, offset)
        return SuccessData(data=data)
    except Exception as e:
        return ParameterException(status_message=str(e))


@api.route('/count', methods=['GET'])
def count():
    args = request.args
    job_name = args.get('job_name')
    if job_name:
        total = CommentInfo.query.filter(CommentInfo.job_name==job_name).count()
        success = CommentInfo.query.filter(CommentInfo.job_name==job_name, CommentInfo.comment_status==1).count()
        failed = total - success
        date = today_time()

        today_total = CommentInfo.query.filter(CommentInfo.job_name==job_name, CommentInfo.create_time >= date).count()
        today_success = CommentInfo.query.filter(CommentInfo.create_time >= date,
                                                 CommentInfo.comment_status == 1,
                                                 CommentInfo.job_name==job_name).count()
        today_failed = CommentInfo.query.filter(CommentInfo.create_time >= date,
                                                CommentInfo.comment_status == 2,
                                                CommentInfo.job_name==job_name).count()
    else:
        total = CommentInfo.query.filter().count()
        success = CommentInfo.query.filter_by(comment_status=1).count()
        failed = total - success
        date = today_time()

        today_total = CommentInfo.query.filter(CommentInfo.create_time >= date).count()
        today_success = CommentInfo.query.filter(CommentInfo.create_time >= date, CommentInfo.comment_status == 1).count()
        today_failed = CommentInfo.query.filter(CommentInfo.create_time >= date, CommentInfo.comment_status == 2).count()

    data = {
        'total': total,
        'success': success,
        'failed': failed,
        'today_total': today_total,
        'today_success': today_success,
        'today_failed': today_failed,
    }
    return SuccessData(data=data)









# 多条件查询
def get_commment_info(start_date, end_date, status, job_name, mp_name, limit, offset):
    condition = []
    if start_date and int(start_date) > 0:
        condition.append(CommentInfo.create_time >= int(start_date))
        condition.append(CommentInfo.create_time <= int(end_date))
    if job_name:
        condition.append(CommentInfo.job_name == job_name)
    if mp_name:
        condition.append(CommentInfo.mp_name == mp_name)
    if int(status) == 0:
        res = CommentInfo.query.filter(*condition).order_by(CommentInfo.create_time.desc()).limit(limit).offset(offset).all()
        count = CommentInfo.query.count()
    else:
        condition.append(CommentInfo.comment_status == status)
        res = CommentInfo.query.filter(*condition).order_by(CommentInfo.create_time.desc()).limit(limit).offset(offset).all()
        count = CommentInfo.query.filter(*condition).count()
    datas = []
    for r in res:
        data = r.to_dict()
        record = Record.query.filter_by(biz=r.biz).first()
        data.update({'ver_info_html': record.ver_info_html if record else ''})
        datas.append(data)
    return {
            'count': count,
            'data': datas
            }
