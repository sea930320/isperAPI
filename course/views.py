#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging

import re
import xlrd
import xlwt

from account.models import TClass, TRole
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, EmptyPage
from django.utils.http import urlquote

from django.db.models import Q, Count
from django.http import HttpResponse
from course.models import *
from group.models import AllGroups
from project.models import Project
from team.models import TeamMember
from utils import code, const, query
from utils.request_auth import auth_check

logger = logging.getLogger(__name__)


# 课程列表
def api_course_list(request):

    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字

        if search:
            qs = Course.objects.filter(Q(Q(name__icontains=search) | Q(teacher__name__icontains=search) | Q(courseId__icontains=search)) & Q(del_flag=0))
        else:
            qs = Course.objects.all(del_flag=0)

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
                Q(courseName__icontains=search) &
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
                'courseName': flow.courseName + '-' + flow.teacher.name + '-' + flow.courseId,
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
