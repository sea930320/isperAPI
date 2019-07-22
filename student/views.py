#!/usr/bin/python
# -*- coding=utf-8 -*-

# from django.shortcuts import
import json
import logging
import random
from platform import node
import re
import xlrd
import xlwt
from django.utils.http import urlquote

from django.utils.timezone import now

from account.models import Tuser, TNotifications, TInnerPermission
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, F, Count
from django.http import HttpResponse
from business.models import *
from student.models import *
from course.models import *
from business.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from student.models import *
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation, \
    FlowRoleAllocationAction, ProcessRoleAllocationAction, FlowNodeSelectDecide, SelectDecideItem
from workflow.service import get_start_node, bpmn_color
from datetime import datetime
from django.utils import timezone
import random
import string
from utils.public_fun import getProjectIDByGroupManager, \
    getProjectIDByCompanyManager, \
    getProjectIDByCompanyManagerAssistant, \
    getProjectIDByGroupManagerAssistant
from django.forms.models import model_to_dict
from socketio.socketIO_client import SocketIO, LoggingNamespace
import codecs
import pypandoc
from system.models import UploadFile
import html2text

logger = logging.getLogger(__name__)


def api_student_watch_business_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数
        type = int(request.GET.get("type", 0))  # 实验状态

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        linkedCompanyIds = UniversityLinkedCompany.objects.filter(university=user.tcompany).values_list(
            'linked_company_id', flat=True).distinct()

        if type == 0:
            qs = Business.objects.filter(
                Q(del_flag=0, target_company__in=linkedCompanyIds) | Q(del_flag=0,
                                                                       target_part__company__in=linkedCompanyIds))
        elif type == 1:
            qs = Business.objects.filter(
                Q(del_flag=0, target_company__in=linkedCompanyIds) | Q(del_flag=0,
                                                                       target_part__company__in=linkedCompanyIds)).exclude(
                studentwatchingbusiness__university=user.tcompany,
                studentwatchingbusiness__team__members__id=user.pk)
        else:
            qs = Business.objects.filter(studentwatchingbusiness__university=user.tcompany,
                                         studentwatchingbusiness__team__members__id=user.pk)

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(pk__icontains=search))
            qs = qs.filter(del_flag=0)

        paginator = Paginator(qs, size)

        try:
            businesses = paginator.page(page)
        except EmptyPage:
            businesses = paginator.page(1)

        results = []

        for item in businesses:
            isWatching = item.studentwatchingbusiness_set.filter(university=user.tcompany,
                                                                 team__members__id=user.pk).count() > 0
            project = Project.objects.filter(pk=item.project_id).first()
            if project:
                project_dict = {
                    'id': project.id, 'name': project.name,
                    'office_item': project.officeItem.name if project.officeItem else None
                }
            else:
                project_dict = None

            node = FlowNode.objects.filter(pk=item.node_id).first() if item.node else None
            if node:
                cur_node = {
                    'id': node.id, 'name': node.name, 'condition': node.condition,
                    'process_type': node.process.type if node.process else None,
                }
            else:
                cur_node = None

            company = item.target_company if item.target_company else item.target_part.company if item.target_part else None
            company = {'id': company.pk, 'name': company.name} if company else None
            business = {
                'id': item.id, 'name': item.name, 'show_nickname': item.show_nickname,
                'start_time': item.start_time.strftime('%Y-%m-%d') if item.start_time else None,
                'end_time': item.end_time.strftime('%Y-%m-%d') if item.end_time else None,
                'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else None,
                'status': item.status, 'created_by': user_simple_info(item.created_by_id),
                'node_id': item.node_id, 'company': company,
                'project': project_dict,
                'huanxin_id': item.huanxin_id,
                'node': cur_node, 'flow_id': project.flow_id if project else None,
                'officeItem': model_to_dict(item.officeItem) if item.officeItem else None,
                'jumper_id': item.jumper_id, 'is_watching': isWatching
            }
            results.append(business)

        paging = {
            'count': paginator.count,
            'has_previous': businesses.has_previous(),
            'has_next': businesses.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': businesses.number,
            'page_size': size
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_watch_business_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_watch_course_list(request):
    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        qs = Course.objects.filter(tcompany=user.tcompany, type=0)
        data = [{
            'value': item.id,
            'text': item.courseName,
            'courseId': item.courseId,
            'courseSeqNum': item.courseSeqNum,
            'courseSemester': item.courseSemester,
            'teacherName': item.teacher.name if item.teacher else None,
            'teacher': model_to_dict(item.teacher, fields=['id', 'name', 'username']) if item.teacher else None,
            'courseCount': item.courseCount,
            'experienceTime': item.experienceTime,
            'studentCount': item.studentCount,
            'create_time': item.create_time.strftime('%Y-%m-%d') if item.create_time else None,
        } for item in qs]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': data}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_watch_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_watch_company_user_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        qs = Tuser.objects.filter(tcompany=user.tcompany, roles=9, del_flag=0)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(username__icontains=search))
            qs = qs.filter(del_flag=0)

        paginator = Paginator(qs, size)

        try:
            users = paginator.page(page)
        except EmptyPage:
            users = paginator.page(1)

        results = []

        for item in users:
            result = model_to_dict(item, fields=['id', 'username', 'name', 'student_id', 'gender'])
            result['class'] = model_to_dict(item.tclass) if item.tclass else None
            result['page'] = page
            results.append(result)

        paging = {
            'count': paginator.count,
            'has_previous': users.has_previous(),
            'has_next': users.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': users.number,
            'page_size': size
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_watch_company_user_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_business_team_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id", None)
        if business_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        qs = StudentWatchingTeam.objects.filter(studentwatchingbusiness__university=user.tcompany,
                                                studentwatchingbusiness__business__id=business_id, type=0, del_flag=0)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(username__icontains=search))
            qs = qs.filter(del_flag=0)

        paginator = Paginator(qs, size)

        try:
            teams = paginator.page(page)
        except EmptyPage:
            teams = paginator.page(1)

        results = []

        for item in teams:
            result = model_to_dict(item, fields=['id', 'name', 'type'])
            result['team_leader'] = model_to_dict(item.team_leader,
                                                  fields=['id', 'name', 'username']) if item.team_leader else None
            result['create_time'] = item.create_time.strftime('%Y-%m-%d') if item.create_time else None
            results.append(result)

        paging = {
            'count': paginator.count,
            'has_previous': teams.has_previous(),
            'has_next': teams.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': teams.number,
            'page_size': size
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_business_team_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_teacher_list(request):
    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        qs = Tuser.objects.filter(tcompany=user.tcompany, teacher_id__isnull=False, roles=4)
        data = [{
            'value': item.id,
            'text': item.name,
            'username': item.username,
            'teacher_id': item.teacher_id
        } for item in qs]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': data}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_teacher_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_watch_start(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user = request.user
        watch_config = request.POST.get("watch_config", None)
        if watch_config is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        watch_config = json.loads(watch_config)
        sel_business = Business.objects.get(pk=watch_config['selected_business']['id'])
        if watch_config['team_mode'] == 0:
            sel_team = StudentWatchingTeam.objects.get(pk=watch_config['selected_team']['id'])
        else:
            new_team = watch_config(['new_team'])
            sel_team = StudentWatchingTeam.objects.create(university=user.tcompany, name=new_team['name'],
                                                          type=new_team['public_mode'], team_leader=user)
            for sel_user in new_team['users']:
                tuser = Tuser.objects.filter(pk=sel_user.id).first()
                if not tuser:
                    continue
                sel_team.members.add(tuser)

        sel_team.members.add(user)
        is_created = False
        if watch_config['mode'] == 0:
            sel_course = Course.objects.get(pk=watch_config['selected_course'])
            if (
            StudentWatchingBusiness.objects.filter(university=user.tcompany, course=sel_course, business=sel_business,
                                                   team=sel_team).first()):
                is_created = True
        else:
            extra_course = watch_config['extra_course']
            sel_course = Course.objects.create(courseName=extra_course['name'],
                                               teacher=Tuser.objects.get(pk=extra_course['teacher']), created_by=user, type=2)
        if not is_created:
            StudentWatchingBusiness.objects.create(university=user.tcompany, course=sel_course, business=sel_business,
                                                   team=sel_team, created_by=request.user)
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_survey_set_select_questions Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
