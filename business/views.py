#!/usr/bin/python
# -*- coding=utf-8 -*-
import json
import logging

from account.models import Tuser
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponse
from experiment.models import *
from business.models import *
from experiment.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation
from workflow.service import get_start_node, bpmn_color
from datetime import datetime
import random
import string
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters= string.ascii_lowercase
    return ''.join(random.sample(letters,stringLength))

def api_business_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID

        project = Project.objects.get(pk=project_id)

        # 判断项目是否存在
        if project:
            # 验证项目中是否有未配置的跳转项目
            if not check_jump_project(project):
                resp = code.get_msg(code.EXPERIMENT_JUMP_PROJECT_SETUP_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            with transaction.atomic():
                business = Business.objects.create(project=project, name=project.name,
                                                cur_project_id=project_id, created_by=request.user)
                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': business.id, 'name': u'{0} {1}'.format(business.id, business.name), 'project_id': business.project_id,
                    'show_nickname': business.show_nickname, 'start_time': business.start_time, 'end_time': business.end_time, 'status': business.status, 'created_by': user_simple_info(business.created_by),
                    'course_class_id': model_to_dict(project.course) if project.course else '', 'node_id': business.node_id,
                    'create_time': business.create_time.strftime('%Y-%m-%d')
                }
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")