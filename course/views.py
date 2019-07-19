#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging
import os

import re
import xlrd
import xlwt

from account.models import TClass, TRole, TNotifications
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, EmptyPage
from django.utils.http import urlquote

from django.db.models import Q, Count
from django.http import HttpResponse, Http404
from course.models import *
from group.models import AllGroups
from project.models import Project
from team.models import TeamMember
from utils import code, const, query
from utils.request_auth import auth_check
from django.conf import settings

logger = logging.getLogger(__name__)


# 课程列表
def api_course_list(request):

    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字

        if search:
            qs = Course.objects.filter(Q(Q(courseName__icontains=search) | Q(teacher__name__icontains=search) | Q(courseId__icontains=search)) & Q(del_flag=0))
        else:
            qs = Course.objects.filter(del_flag=0)

        data = [{'value': item.id, 'text': item.courseName + '-' + item.teacher.name + '-' + item.courseId} for item in qs]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': data}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_full_list(request):

    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        if search:
            qs = Course.objects.filter(
                Q(Q(courseName__icontains=search) | Q(teacher__name__icontains=search) | Q(courseId__icontains=search)) &
                Q(del_flag=0) &
                Q(tcompany=request.user.tcompanymanagers_set.get().tcompany)
            )
        else:
            qs = Course.objects.filter(Q(del_flag=0) & Q(tcompany=request.user.tcompanymanagers_set.get().tcompany))

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = [{
                'id': flow.id,
                'courseId': flow.courseId,
                'courseName': flow.courseName,
                'courseFullName': flow.courseName + '-' + flow.teacher.name + '-' + flow.courseId,
                'courseSeqNum': flow.courseSeqNum,
                'courseSemester': flow.courseSemester,
                'teacherName': flow.teacher.name,
                'teacherId': flow.teacher.teacher_id,
                'courseCount': flow.courseCount,
                'experienceTime': flow.experienceTime,
                'studentCount': flow.studentCount,
                'created_by': flow.created_by.username,
                'create_time': flow.create_time.strftime('%Y-%m-%d'),
            } for flow in flows]

            paging = {
                'count': paginator.count,
                'has_previous': flows.has_previous(),
                'has_next': flows.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': flows.number,
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_groups_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_save_new(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        courseId = request.POST.get("courseId")
        courseName = request.POST.get("courseName")
        courseSeqNum = request.POST.get("courseSeqNum")
        courseSemester = request.POST.get("courseSemester")
        teacherName = request.POST.get("teacherName")
        teacherId = request.POST.get("teacherId")
        courseCount = request.POST.get("courseCount")
        experienceTime = request.POST.get("experienceTime")
        studentCount = request.POST.get("studentCount")

        user = AllGroups.objects.get(id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.create(
            username=teacherName + '-' + teacherId,
            name=teacherName,
            teacher_id=teacherId,
            password=make_password('1234567890'),
            tcompany=request.user.tcompanymanagers_set.get().tcompany,
            is_review=1,
        )
        user.roles.add(TRole.objects.get(id=4))

        Course.objects.create(
            courseId=courseId,
            courseName=courseName,
            courseSeqNum=int(courseSeqNum),
            courseSemester=courseSemester,
            teacher=user,
            courseCount=int(courseCount),
            experienceTime=experienceTime,
            studentCount=int(studentCount),
            tcompany_id=request.user.tcompanymanagers_set.get().tcompany.id,
            created_by=request.user,
        )

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_save_edit(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id")
        courseName = request.POST.get("courseName")
        courseSemester = request.POST.get("courseSemester")
        courseCount = request.POST.get("courseCount")
        experienceTime = request.POST.get("experienceTime")

        Course.objects.filter(pk=id).update(
            courseName=courseName,
            courseSemester=courseSemester,
            courseCount=courseCount,
            experienceTime=experienceTime
        )

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_get_teacher_list(request):

    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        teachers = AllGroups.objects.get(id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.filter(
            tcompany_id=request.user.tcompanymanagers_set.get().tcompany.id,
            teacher_id__isnull=False
        )

        list = [{
            'value': user.id,
            'text': user.name
        } for user in teachers]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': list}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_save_teacher_change(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id")
        teacher = request.POST.get("teacher")

        Course.objects.filter(pk=id).update(teacher_id=teacher)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_delete_course(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        ids = eval(request.POST.get("ids", '[]'))

        Course.objects.filter(pk__in=ids).update(del_flag=1)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_course_download_excel(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    file_path = os.path.join(settings.MEDIA_ROOT, u'课堂列表.xls')
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'attachment; filename="课堂列表.xls"'
            return response
    raise Http404


def api_course_excel_data_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        excelData = request.POST.get("excelData", None)

        for item in json.loads(excelData):
            courseId = str(item[u'courseId']).encode('utf8')
            courseName = str(item[u'courseName']).encode('utf8')
            courseSeqNum = int(item[u'courseSeqNum'])
            courseSemester = str(item[u'courseSemester']).encode('utf8')
            teacherName = str(item[u'teacherName']).encode('utf8')
            teacherId = str(item[u'teacherId']).encode('utf8')
            courseCount = int(item[u'courseCount'])
            experienceTime = str(item[u'experienceTime']).encode('utf8')
            studentCount = int(item[u'studentCount'])

            user = AllGroups.objects.get(id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.create(
                username=teacherName + '-' + teacherId,
                name=teacherName,
                teacher_id=teacherId,
                password=make_password('1234567890'),
                tcompany=request.user.tcompanymanagers_set.get().tcompany,
                is_review=1,
            )
            user.roles.add(TRole.objects.get(id=4))

            Course.objects.create(
                courseId=courseId,
                courseName=courseName,
                courseSeqNum=int(courseSeqNum),
                courseSemester=courseSemester,
                teacher=user,
                courseCount=int(courseCount),
                experienceTime=experienceTime,
                studentCount=int(studentCount),
                tcompany_id=request.user.tcompanymanagers_set.get().tcompany.id,
                created_by=request.user,
            )

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_company_excelUsers Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_get_init_attention_data(request):

    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        if search:
            qs = UniversityLinkedCompany.objects.filter(university=request.user.tcompanymanagers_set.get().tcompany, linked_company__name__icontains=search)
        else:
            qs = UniversityLinkedCompany.objects.filter(university=request.user.tcompanymanagers_set.get().tcompany)

        groupID = request.user.tcompanymanagers_set.get().tcompany.group_id
        clist = [{'value': item.id, 'text': item.name} for item in TCompany.objects.filter(Q(group_id=groupID, is_default=0) & ~Q(companyType__name='学校'))]

        paginator = Paginator(qs, size)

        try:
            flows = paginator.page(page)
        except EmptyPage:
            flows = paginator.page(1)

        results = [{
            'id': flow.id,
            'linked_company': flow.linked_company.name,
            'setter': flow.seted_company_manager.username if flow.seted_company_manager is not None else '',
            'created_by': flow.created_by.username,
            'create_time': flow.create_time.strftime('%Y-%m-%d'),
            'seted_time': flow.seted_time.strftime('%Y-%m-%d') if flow.seted_time is not None else '',
            'message': flow.message,
            'status': '申请中' if flow.status == 0 else '已关注' if flow.status == 1 else '已拒绝' if flow.status == 2 else '取消已关注'
        } for flow in flows]

        paging = {
            'count': paginator.count,
            'has_previous': flows.has_previous(),
            'has_next': flows.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': flows.number,
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'companyList': clist, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_groups_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_send_request_data(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        requestMsg = request.POST.get("requestMsg")
        targetCompany = request.POST.get("targetCompany")

        newRequest = UniversityLinkedCompany.objects.create(
            university=request.user.tcompanymanagers_set.get().tcompany,
            linked_company_id=targetCompany,
            created_by=request.user,
            message=requestMsg,
            status=0
        )

        newNotification = TNotifications.objects.create(
            type='attentionRequest_' + str(newRequest.id),
            content=request.user.tcompanymanagers_set.get().tcompany.name + '单位申请了关注我单位业务。',
            link='request-check',
            role=TRole.objects.get(id=3),
            mode=0
        )

        for userItem in TCompany.objects.get(id=targetCompany).tcompanymanagers_set.all():
            newNotification.targets.add(userItem.tuser)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课程列表
def api_course_send_cancel_data(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        ids = eval(request.POST.get("ids", '[]'))

        UniversityLinkedCompany.objects.filter(pk__in=ids).update(status=3)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
