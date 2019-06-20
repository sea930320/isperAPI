#!/usr/bin/python
# -*- coding=utf-8 -*-

# from django.shortcuts import
import json
import logging
import random

from account.models import Tuser, TNotifications, TInnerPermission
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count
from django.http import HttpResponse
from business.models import *
from business.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation, \
    FlowRoleAllocationAction, ProcessRoleAllocationAction
from workflow.service import get_start_node, bpmn_color
from datetime import datetime
import random
import string
from utils.public_fun import getProjectIDByGroupManager
from django.forms.models import model_to_dict
from socketio.socketIO_client import SocketIO, LoggingNamespace

logger = logging.getLogger(__name__)

import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt


# @csrf_exempt
def save_message(request):
    """
        实验发送消息
    """
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        # msg_obj = json.loads(request.body.decode('utf-8'))
        # print msg_obj
        # user_id = int(msg_obj['user_id']) if 'user_id' in msg_obj else None
        # login_type = int(msg_obj['login_type']) if 'login_type' in msg_obj else None
        # business_id = int(msg_obj['business_id']) if 'business_id' in msg_obj else None
        # node_id = int(msg_obj['node_id']) if 'node_id' in msg_obj else None
        # role_alloc_id = int(msg_obj['role_alloc_id']) if 'role_alloc_id' in msg_obj else None
        # type = msg_obj['type'] if 'type' in msg_obj else None
        # msg = msg_obj['msg'] if 'msg' in msg_obj else None
        # cmd = msg_obj['cmd'] if 'cmd' in msg_obj else None
        # param = msg_obj['param'] if 'param' in msg_obj else None
        # file_id = int(msg_obj['file_id']) if 'file_id' in msg_obj else None
        # data = msg_obj['data'] if 'data' in msg_obj else None

        business_id = request.POST.get("business_id", None)
        node_id = request.POST.get("node_id", None)
        role_alloc_id = request.POST.get("role_alloc_id", None)
        type = request.POST.get("type", None)
        msg = request.POST.get("msg", '')
        cmd = request.POST.get("cmd", None)
        param = request.POST.get("param", None)
        file_id = request.POST.get("file_id", None)
        data = request.POST.get('data', None)
        logger.info('business_id:%s,node_id:%s,role_id:%s,type:%s,cmd:%s,param:%s,file_id:%s,'
                    'data:%s' % (business_id, node_id, role_alloc_id, type, cmd, param, file_id, data))

        logger.info('experiment_id:%s,node_id:%s,role_alloc_id:%s,type:%s,cmd:%s,param:%s,file_id:%s,'
                    'data:%s' % (business_id, node_id, role_alloc_id, type, cmd, param, file_id, data))
        user = request.user
        from_obj = str(request.user.pk)
        user_id = user.id
        if not all(v is not None for v in [user_id, business_id, node_id, role_alloc_id]):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        bra = BusinessRoleAllocation.objects.filter(pk=role_alloc_id, business_id=business_id,
                                                    project_id=business.cur_project_id).first()
        if bra is None:
            resp = code.get_msg(code.BUSINESS_ROLE_ALLOCATE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        path = BusinessTransPath.objects.filter(business_id=business_id).last()
        if path is None:
            resp = code.get_msg(code.BUSINESS_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        brat = BusinessRoleAllocationStatus.objects.filter(business_role_allocation_id=role_alloc_id,
                                                           business_id=business_id, path_id=path.pk).first()
        # 是否有结束环节的权限
        can_terminate = bra.can_terminate
        if path.control_status == 2 and can_terminate is False:
            if type == const.MSG_TYPE_TXT or type == const.MSG_TYPE_AUDIO:
                if brat.speak_times == 0:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if cmd == const.ACTION_DOC_SHOW:
                if brat.show_status != 1:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if cmd == const.ACTION_DOC_SUBMIT:
                if brat.submit_status != 1:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        node = FlowNode.objects.filter(pk=business.node_id, del_flag=0).first()
        bps = BusinessPositionStatus.objects.filter(business_id=business_id, business_role_allocation_id=role_alloc_id,
                                                    path_id=path.id).first()
        if bps:
            if bps.sitting_status:
                bps.sitting_status = const.SITTING_DOWN_STATUS
        pos = None
        project = Project.objects.get(pk=business.cur_project_id)
        node = FlowNode.objects.filter(pk=business.node_id, del_flag=0).first()
        role = bra.role
        pos = get_role_position(business, project, node, path, role, role_alloc_id)
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        opt = None
        image = get_role_image(bra.flow_role_alloc_id)
        if image is None:
            resp = code.get_msg(code.EXPERIMENT_ROLE_IMAGE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if type == const.MSG_TYPE_TXT:
            if node.process.type == 1:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                    # 文本， 角色未入席不能说话
                if brat.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                msg = msg.strip()
                if msg == '' or len(msg) > 30000:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                msg = tools.filter_invalid_str(msg)
                msg_obj = {'type': const.MSG_TYPE_TXT, 'msg': msg}
                ext = {'business_id': business_id, 'node_id': node_id, 'username': user.name,
                       'role_alloc_id': role_alloc_id, 'role_name': bra.role.name, 'avatar': image['avatar'],
                       'cmd': const.ACTION_TXT_SPEAK, 'param': '', 'time': time, 'can_terminate': can_terminate,
                       'code_position': pos['code_position'] if pos else ''}
                ext['business_role_alloc'] = model_to_dict(
                    BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first())
        msgDict = {}
        message = None
        if role_alloc_id:
            message = BusinessMessage.objects.create(business_id=business_id, user_id=user_id,
                                                     business_role_allocation_id=role_alloc_id,
                                                     file_id=file_id, msg=msg, msg_type=type,
                                                     path_id=path.id, user_name=user.name, role_name=bra.role.name,
                                                     ext=json.dumps(ext))
        ext['id'] = message.pk
        ext['opt_status'] = False
        msgDict = model_to_dict(message) if message else {}
        msgDict['ext'] = ext
        msgDict['data'] = msgDict['msg']
        msgDict['from'] = message.user.id
        msgDict['type'] = 'groupchat'
        msgDict['to'] = None

        resp = code.get_msg(code.SUCCESS)
        # resp['d'] = msgDict
        with SocketIO(u'localhost', 4000, LoggingNamespace) as socketIO:
            socketIO.emit('message', msgDict)
            socketIO.wait_for_callbacks(seconds=1)
        if can_terminate is False:
            # 角色发言次数减1
            if path.control_status == 2 and type != const.MSG_TYPE_CMD:
                brat.speak_times -= 1
                brat.save(update_fields=['speak_times'])
    except Exception as e:
        logger.exception('save_message Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
