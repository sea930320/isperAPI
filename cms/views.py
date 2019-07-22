#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging

from cms.models import TMsg, TBusinessMsg
from django.db.models import Q
from django.http import HttpResponse
from utils import code
from utils.request_auth import auth_check
from business.service import *

logger = logging.getLogger(__name__)


def api_cms_new_msg_num_business(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user_id = request.GET.get("user_id", None)  # 用户ID
        business_id = request.GET.get("business_id", None)  # 实验id

        msgs = TBusinessMsg.objects.filter(to_user_id=user_id, business_id=business_id, read_status=0)  # 未读信息

        data_count = len(msgs)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data_count
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_cms_new_msg_num_business Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 群发消息
def api_cms_send_msg_business(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        from_user_id = request.POST.get("from_user_id", None)  # 发件人ID
        to_user_ids = request.POST.get("to_user_ids", None)  # 收件人IDs,用逗号连接
        business_id = request.POST.get("business_id", None)  # 实验id
        content = request.POST.get("content", None)  # 内容
        host_id = request.POST.get("host_id", None)  # 主题贴ID

        # 参数check
        if None in (from_user_id, to_user_ids, content):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        to_user_id_arr = to_user_ids.split(',')  # 根据逗号拆分
        for to_user_id in to_user_id_arr:
            msg, flag = TBusinessMsg.objects.update_or_create(from_user_id=from_user_id, to_user_id=to_user_id,
                                                              content=content,
                                                              host_id=host_id, business_id=business_id)

        data = {'id': msg.id, 'from_user': msg.from_user.name, 'to_user': msg.to_user.name, 'content': msg.content,
                'create_time': msg.create_time.strftime('%Y-%m-%d %H:%M:%S')}
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_cms_send_msg_business Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 消息列表
def api_cms_msg_list_business(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user_id = request.GET.get("user_id", None)  # 用户ID
        business_id = request.GET.get("business_id", None)  # 实验id
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        msgs = TBusinessMsg.objects.filter(host=None, business_id=business_id) \
            .filter(Q(to_user_id=user_id) | Q(from_user_id=user_id, ))  # 收件列表

        data_count = len(msgs)
        results = []  # 返回数据
        bc = data_count % size
        if bc == 0:
            pages = data_count / size
        else:
            pages = (data_count / size) + 1 if bc < size else 0  # 总页数
        paging = {
            'count': data_count,
            'has_previous': True if page > 1 else False,
            'has_next': True if page < pages else False,
            'num_pages': pages,
            'cur_page': page,
            'page_size': size
        }
        if page > pages:
            results = []
        else:
            start = (page - 1) * size
            end = page * size
            if end > data_count:
                end = data_count
            # 遍历主题帖构造回复贴的楼层数据
            for i in range(start, end):
                msg = msgs[i]
                reply_list = TBusinessMsg.objects.filter(host_id=msg.pk).order_by('create_time')  # 回复贴列表, 时间升序
                reply_data = []
                for reply in reply_list:
                    reply_data.append({
                        'id': reply.id,
                        'from_user_name': reply.from_user.name,
                        'from_user_id': reply.from_user.id,
                        'to_user_name': reply.to_user.name,
                        'to_user_id': reply.to_user.id,
                        'content': reply.content, 'read_status': reply.read_status,
                        'create_time': reply.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    # 如果自己是收件人，则将消息置为已读状态
                    print user_id
                    print reply.to_user.id
                    if str(reply.to_user.id) == user_id:
                        reply.read_status = 1
                        reply.save()
                results.append({'id': msg.id, 'from_user_name': msg.from_user.name,
                                'from_user_id': msg.from_user.id,
                                'to_user_name': msg.to_user.name, 'to_user_id': msg.to_user.id,
                                'content': msg.content, 'read_status': msg.read_status,
                                'create_time': msg.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'reply': reply_data})
                msg.read_status = 1
                msg.save()  # 更新阅读状态

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'paging': paging, 'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_cms_msg_list_business Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 根据实验任务收件人列表
def api_cms_to_user_list_business(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id", None)  # 实验任务id
        business = Business.objects.get(pk=business_id)  # 实验任务id
        btmsQs = BusinessTeamMember.objects.filter(business_id=business_id, del_flag=0, project_id=business.cur_project_id)
        btms = []
        for btm in btmsQs:
            btms.append({
                'user_id': btm.user.id,
                'user_name': btm.user.name,
                'role_id': btm.business_role.id,
                'role_name': btm.business_role.name,
                'no': btm.no
            })

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = btms
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_cms_to_user_list_business Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")