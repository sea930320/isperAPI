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
        if login_type not in [5, 9]:
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
            ids = Business.objects.filter(studentwatchingbusiness__university=user.tcompany,
                                          studentwatchingbusiness__team__members__id=user.pk).values_list('id',
                                                                                                          flat=True).distinct()
            qs = Business.objects.filter(pk__in=ids)

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
        if login_type not in [5, 9]:
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


def api_student_team_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id", None)

        if business_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if login_type == 9:
            stwbs = StudentWatchingBusiness.objects.filter(university=user.tcompany, business_id=business_id)
        elif login_type == 5:
            stwbs = StudentWatchingBusiness.objects.filter(business_id=business_id)
        teams = []
        for stwb in stwbs:
            stwt = StudentWatchingTeam.objects.filter(pk=stwb.team_id).first()
            if stwt is None:
                continue
            teacher = model_to_dict(stwb.course.teacher, fields=['id', 'username', 'name', 'teacher_id', 'gender'])
            members = [model_to_dict(member, fields=['id', 'username', 'name', 'student_id', 'gender']) for member in
                       stwt.members.all()]
            team = {'teacher': teacher, 'members': members, 'name': stwt.name, 'id': stwt.id,
                    'create_time': stwt.create_time.strftime('%Y-%m-%d') if stwt.create_time else None,
                    'leader': model_to_dict(stwt.team_leader,
                                            fields=['id', 'username', 'name',
                                                    'student_id', 'gender'])}
            teams.append(team)
        resp = code.get_msg(code.SUCCESS)
        data = get_business_detail(business)
        resp['d'] = {'results': teams, 'business': data}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_team_detail Exception:{0}'.format(str(e)))
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
        if login_type not in [5, 9]:
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
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        ids = StudentWatchingTeam.objects.filter(studentwatchingbusiness__university=user.tcompany,
                                                 studentwatchingbusiness__business__id=business_id, type=0,
                                                 del_flag=0).values_list('id', flat=True).distinct()
        qs = StudentWatchingTeam.objects.filter(pk__in=ids)
        if search:
            qs = qs.filter(Q(name__icontains=search))

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


def api_student_team_my_list(request):
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

        qs = StudentWatchingTeam.objects.filter(university=user.tcompany, del_flag=0, members__id=user.id)
        if search:
            qs = qs.filter(Q(name__icontains=search))

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
        logger.exception('api_student_team_my_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_team_available_list(request):
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

        qs = StudentWatchingTeam.objects.filter(university=user.tcompany, del_flag=0).exclude(members__id=user.id)
        if search:
            qs = qs.filter(Q(name__icontains=search))

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
        logger.exception('api_student_team_available_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_teacher_list(request):
    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
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
            new_team = watch_config['new_team']
            sel_team = StudentWatchingTeam.objects.create(university=user.tcompany, name=new_team['name'],
                                                          type=new_team['public_mode'], team_leader=user)
            for sel_user in new_team['users']:
                tuser = Tuser.objects.filter(pk=sel_user['id']).first()
                if not tuser:
                    continue
                sel_team.members.add(tuser)

        sel_team.members.add(user)
        is_created = False
        if watch_config['mode'] == 0:
            sel_course = Course.objects.get(pk=watch_config['selected_course'])
            stwb = StudentWatchingBusiness.objects.filter(university=user.tcompany, course=sel_course,
                                                          business=sel_business,
                                                          team=sel_team).first()
            if (stwb):
                is_created = True
        else:
            extra_course = watch_config['extra_course']
            sel_course = Course.objects.create(courseName=extra_course['name'],
                                               teacher=Tuser.objects.get(pk=extra_course['teacher']), created_by=user,
                                               type=2, tcompany=user.tcompany)
        if not is_created:
            stwb = StudentWatchingBusiness.objects.create(university=user.tcompany, course=sel_course,
                                                          business=sel_business,
                                                          team=sel_team, created_by=request.user)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'results': stwb.id
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_survey_set_select_questions Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_request_assist(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        business_id = request.POST.get("business_id", None)
        job_user_id = request.POST.get("job_user_id", None)
        if None in [business_id, job_user_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        isRequestExist = StudentRequestAssistStatus.objects.filter(business_id=business_id, university=user.tcompany,
                                                                   requestedFrom=user, status__in=[0, 1]).count()
        if isRequestExist > 0:
            resp = code.get_msg(code.REQUEST_ALREADY_EXISTS)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        StudentRequestAssistStatus.objects.update_or_create(business_id=business_id, university=user.tcompany,
                                                            requestedFrom=user,
                                                            requestedTo_id=job_user_id, status=0)

        srases = StudentRequestAssistStatus.objects.filter(business_id=business_id, university=user.tcompany,
                                                           requestedFrom_id=user.id, del_flag=0)
        results = []
        for sras in srases:
            requestedTo = {
                'id': sras.requestedTo_id,
                'name': sras.requestedTo.name if sras.requestedTo is not None else '',
                'username': sras.requestedTo.username if sras.requestedTo is not None else '',
                'type': sras.requestedTo.type if sras.requestedTo is not None else '',
                'gender': sras.requestedTo.gender if sras.requestedTo is not None else '',
                'position': model_to_dict(
                    sras.requestedTo.tposition) if sras.requestedTo is not None and sras.requestedTo.tposition else None
            }
            results.append({
                "id": sras.id,
                "business_id": business_id,
                "university": model_to_dict(user.tcompany, fields=['name', 'comment', 'created_by_id']),
                "requestedTo": requestedTo,
                "requestedFrom": model_to_dict(sras.requestedFrom,
                                               fields=['id', 'name', 'username']) if sras.requestedFrom else None,
                "status": sras.status,
                'create_time': sras.create_time.strftime('%Y-%m-%d') if sras.create_time else None,
            })
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'results': results
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_request_assist Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_request_assist_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        id = request.POST.get("id", None)
        status = request.POST.get("status", None)
        del_flag = int(request.POST.get("del_flag", 0))
        if None in [id, status]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        sras = StudentRequestAssistStatus.objects.filter(pk=id).first()
        if not sras:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        sras.status = status
        sras.del_flag = del_flag
        sras.save()
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_request_assist Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_request_assist_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        business_id = request.GET.get("business_id", None)
        if None in [business_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if login_type == 9:
            srases = StudentRequestAssistStatus.objects.filter(business_id=business_id, university=user.tcompany,
                                                               requestedFrom_id=user.id, del_flag=0)
        elif login_type == 5:
            srases = StudentRequestAssistStatus.objects.filter(business_id=business_id,
                                                               requestedTo_id=user.id, del_flag=0)

        results = []
        for sras in srases:
            requestedTo = {
                'id': sras.requestedTo_id,
                'name': sras.requestedTo.name if sras.requestedTo is not None else '',
                'username': sras.requestedTo.username if sras.requestedTo is not None else '',
                'type': sras.requestedTo.type if sras.requestedTo is not None else '',
                'gender': sras.requestedTo.gender if sras.requestedTo is not None else '',
                'position': model_to_dict(
                    sras.requestedTo.tposition) if sras.requestedTo is not None and sras.requestedTo.tposition else None
            }
            results.append({
                "id": sras.id,
                "business_id": business_id,
                "university": model_to_dict(sras.university, fields=['name', 'comment', 'created_by_id']),
                "requestedTo": requestedTo,
                "requestedFrom": model_to_dict(sras.requestedFrom,
                                               fields=['id', 'name', 'username']) if sras.requestedFrom else None,
                "status": sras.status,
                'create_time': sras.create_time.strftime('%Y-%m-%d') if sras.create_time else None,
            })
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'results': results
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_student_request_assist_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_send_msg(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.POST.get("business_id", None)
        to = request.POST.get("to", None)
        msg = request.POST.get("msg", None)
        msg_type = int(request.POST.get("msg_type", 0))

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [business_id, to, msg]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        fromUser = model_to_dict(user, fields=['id', 'name', 'username'])
        fromUser['login_type'] = login_type
        ext = {'business_id': business_id, "from_user": fromUser, "to": json.loads(to), "msg": msg,
               "msg_type": msg_type}

        scl = StudentChatLog.objects.create(business_id=business_id, from_user=user, msg=msg, msg_type=msg_type,
                                            ext=json.dumps(ext))
        resp = code.get_msg(code.SUCCESS)
        msgDict = ext
        msgDict['id'] = scl.id
        msgDict['create_time'] = scl.create_time.strftime('%Y-%m-%d %H:%M:%S')
        with SocketIO(u'localhost', 4000, LoggingNamespace) as socketIO:
            socketIO.emit('student_message', msgDict)
            socketIO.wait_for_callbacks(seconds=1)
    except Exception as e:
        logger.exception('api_student_send_msg Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_msg_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.GET.get("business_id", None)
        msg_type = int(request.GET.get("msg_type", 0))

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [business_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        scls = StudentChatLog.objects.filter(business_id=business_id, msg_type=msg_type)
        message_list = []
        for m in scls:
            ext = json.loads(m.ext)
            toUsers = ext['to']
            toMe = False
            for to in toUsers:
                if str(to["id"]) == str(user.id):
                    toMe = True
                    break;
            if not toMe:
                continue
            ext['id'] = m.id
            ext['create_time'] = m.create_time.strftime('%Y-%m-%d %H:%M:%S')
            message_list.append(ext)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'results': message_list
        }
    except Exception as e:
        logger.exception('api_student_msg_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_todo_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.GET.get("business_id", None)
        created_by_id = request.GET.get("created_by_id", None)
        student_id = request.GET.get("student_id", None)

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5, 9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [business_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if login_type == 5:
            created_by_id = user.id
        if login_type == 9:
            student_id = user.id

        stl = StudentTodoList.objects.filter(business_id=business_id, del_flag=0)
        if created_by_id is not None:
            stl = stl.filter(created_by_id=created_by_id)
        if student_id is not None:
            stl = stl.filter(student_id=student_id)
        results = []
        for st in stl:
            results.append({
                'id': st.id,
                'created_by': model_to_dict(st.created_by,
                                            fields=['id', 'name', 'username']) if st.created_by else None,
                'student': model_to_dict(st.student,
                                         fields=['id', 'name', 'username']) if st.student else None,
                'name': st.name,
                'create_time': st.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'business_id': st.business_id
            })
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'results': results
        }
    except Exception as e:
        logger.exception('api_student_todo_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_todo_list_add(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.POST.get("business_id", None)
        student_id = request.POST.get("student_id", None)
        name = request.POST.get("name", "")

        user = request.user
        login_type = request.session['login_type']
        if login_type not in [5]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [business_id] or name == "":
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if student_id:
            student_id = int(student_id)
        StudentTodoList.objects.create(business_id=business_id, del_flag=0, created_by=user, student_id=student_id,
                                       name=name)
        resp = code.get_msg(code.SUCCESS)
    except Exception as e:
        logger.exception('api_student_todo_list_add Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_todo_list_remove(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        st_id = request.POST.get("id", None)

        login_type = request.session['login_type']
        if login_type not in [5]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        StudentTodoList.objects.filter(pk=st_id).update(del_flag=1)
        resp = code.get_msg(code.SUCCESS)
    except Exception as e:
        logger.exception('api_student_todo_list_remove Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_todo_list_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        st_id = request.POST.get("id", None)
        student_id = request.POST.get("student_id", None)
        name = request.POST.get("name", "")

        login_type = request.session['login_type']
        if login_type not in [5]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [st_id] or name == "":
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        StudentTodoList.objects.filter(pk=st_id).update(student_id=student_id, name=name)
        resp = code.get_msg(code.SUCCESS)
    except Exception as e:
        logger.exception('api_student_todo_list_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_team_users(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        team_id = request.GET.get("id", None)

        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [team_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        swt = StudentWatchingTeam.objects.filter(pk=team_id).first()
        members = [model_to_dict(member, fields=['id', 'name', 'username']) for member in swt.members.all()]

        qs = Tuser.objects.filter(tcompany=request.user.tcompany, roles__id=9).exclude(pk=request.user.id)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(username__icontains=search))

        paginator = Paginator(qs, size)

        try:
            users = paginator.page(page)
        except EmptyPage:
            users = paginator.page(1)

        university_users = [model_to_dict(student, fields=['id', 'name', 'username']) for student in users]

        paging = {
            'count': paginator.count,
            'has_previous': users.has_previous(),
            'has_next': users.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': users.number,
            'page_size': size
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'members': members,
            'university_users': university_users,
            'paging': paging
        }
    except Exception as e:
        logger.exception('api_student_team_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_team_add_user(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        team_id = request.POST.get("id", None)
        student_id = request.POST.get("student_id", None)

        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [team_id, student_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        swt = StudentWatchingTeam.objects.filter(pk=team_id).first()
        swt.members.add(Tuser.objects.filter(pk=student_id).first())
        resp = code.get_msg(code.SUCCESS)
    except Exception as e:
        logger.exception('api_student_todo_list_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_student_team_remove_user(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        team_id = request.POST.get("id", None)
        student_id = request.POST.get("student_id", None)

        login_type = request.session['login_type']
        if login_type not in [9]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if None in [team_id, student_id]:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        swt = StudentWatchingTeam.objects.filter(pk=team_id).first()
        swt.members.remove(Tuser.objects.filter(pk=student_id).first())
        members = swt.members.all()
        print swt.team_leader.id
        print student_id
        if int(swt.team_leader.id) == int(student_id):
            print members
            if members.count() == 0:
                swt.del_flag =1
            else:
                swt.team_leader = members[0]
            swt.save()
        resp = code.get_msg(code.SUCCESS)
    except Exception as e:
        logger.exception('api_student_todo_list_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
