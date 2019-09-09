#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging
import os

import re
import xlrd
import xlwt

from account.models import TClass, TRole, TNotifications
from business.service import get_business_detail
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, Http404
from course.models import *
from student.models import StudentWatchingBusiness, StudentWatchingTeam
from course.service import *
from business.models import *
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
            qs = Course.objects.filter(Q(Q(courseName__icontains=search) | Q(
                courseId__icontains=search)) & Q(del_flag=0))
        else:
            qs = Course.objects.filter(del_flag=0)

        results = []
        for item in qs:
            teachers = item.teachers.all()
            teachers_label = getTeacherLabels(teachers)

            data = {'value': item.id,
                    'text': (item.courseName + '-' + teachers_label + '-' + item.courseId) if item.courseId else (
                        item.courseName + '-' + teachers_label)}
            results.append(data)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
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
                Q(Q(courseName__icontains=search) | Q(
                    courseId__icontains=search)) &
                Q(del_flag=0) & Q(type=0) &
                Q(tcompany=request.user.tcompanymanagers_set.get().tcompany)
            )
        else:
            qs = Course.objects.filter(
                Q(del_flag=0) & Q(type=0) & Q(tcompany=request.user.tcompanymanagers_set.get().tcompany))

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
                'courseFullName': (flow.courseName if flow.courseName else '') + '-' + getTeacherLabels(
                    flow.teachers.all()) + '-' + (flow.courseId if flow.courseId else ''),
                'courseSeqNum': flow.courseSeqNum,
                'courseSemester': flow.courseSemester,
                'teachers': [model_to_dict(teacher, fields=['id', 'teacher_id', 'name']) for teacher in flow.teachers.all()],
                'students': [model_to_dict(student, fields=['id', 'student_id', 'name']) for student in flow.students.all()],
                'courseCount': flow.courseCount,
                'experienceTime': flow.experienceTime,
                'created_by': flow.created_by.username,
                'create_time': flow.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'linked_business': [{
                    'id': item.id,
                    'name': item.name,
                    'target_company': item.target_company.name if item.target_company else item.target_part.company.name,
                } for item in Business.objects.filter(studentwatchingbusiness__course_id=flow.id).distinct()],
                'linked_team': [{
                    'id': team.id,
                    'name': team.name,
                    'leader': team.team_leader.username,
                    'create_time': team.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'member_count': team.members.count(),
                    'members': [model_to_dict(student, fields=['id', 'student_id', 'name']) for student in team.members.all()],
                    'businesses': [get_business_detail(stwb.business) for stwb in team.studentwatchingbusiness_set.all()]
                } for team in StudentWatchingTeam.objects.filter(studentwatchingbusiness__course_id=flow.id).distinct()]
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
def api_course_outside_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        if search:
            qs = Course.objects.filter(
                Q(Q(courseName__icontains=search) | Q(
                    courseId__icontains=search)) &
                Q(del_flag=0) & Q(type=2) &
                Q(tcompany=request.user.tcompanymanagers_set.get().tcompany)
            )
        else:
            qs = Course.objects.filter(
                Q(del_flag=0) & Q(type=2) & Q(tcompany=request.user.tcompanymanagers_set.get().tcompany))

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
                'courseName': flow.courseName,
                'courseFullName': (flow.courseName if flow.courseName else '') + '-' + getTeacherLabels(
                    flow.teachers.all()) + '-' + (flow.courseId if flow.courseId else ''),
                'teachers': [model_to_dict(teacher, fields=['id', 'name']) for teacher in flow.teachers.all()],
                'students': [model_to_dict(student, fields=['id', 'student_id', 'name']) for student in
                             flow.students.all()],
                'created_by': flow.created_by.username,
                'create_time': flow.create_time.strftime('%Y-%m-%d'),
                'linked_business': [{
                    'id': item.id,
                    'name': item.name,
                    'target_company': item.target_company.name if item.target_company else item.target_part.company.name,
                } for item in Business.objects.filter(studentwatchingbusiness__course_id=flow.id).distinct()],
                'linked_team': [{
                    'id': team.id,
                    'name': team.name,
                    'leader': team.team_leader.username,
                    'create_time': team.create_time.strftime('%Y-%m-%d'),
                    'member_count': team.members.count(),
                } for team in StudentWatchingTeam.objects.filter(studentwatchingbusiness__course_id=flow.id).distinct()]
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
def api_course_hobby_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))
        login_type = request.session['login_type']

        if search:
            qs = Course.objects.filter(
                Q(Q(courseName__icontains=search) | Q(
                    courseId__icontains=search)) &
                Q(del_flag=0) & Q(type=1)
            )
        else:
            qs = Course.objects.filter(
                Q(del_flag=0) & Q(type=1))
        if login_type in [4, 8]:
            qs = qs.filter(created_by=request.user)
        else:
            qs = qs.filter(Q(tcompany=request.user.tcompanymanagers_set.get().tcompany))

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                courses = paginator.page(page)
            except EmptyPage:
                courses = paginator.page(1)

            results = [{
                'id': course.id,
                'courseName': course.courseName,
                'courseSemester': course.courseSemester,
                'courseSeqNum': course.courseSeqNum,
                'courseCount': course.courseCount,
                'experienceTime': course.experienceTime,
                'teachers': [model_to_dict(teacher, fields=['id', 'name']) for teacher in course.teachers.all()],
                'created_by': course.created_by.username,
                'create_time': course.create_time.strftime('%Y-%m-%d'),
                'linked_business': [{
                    'id': item.id,
                    'name': item.name,
                    'target_company': item.target_company.name if item.target_company else item.target_part.company.name,
                } for item in Business.objects.filter(studentwatchingbusiness__course_id=course.id).distinct()],
                'linked_team': [{
                    'id': team.id,
                    'name': team.name,
                    'leader': team.team_leader.username,
                    'create_time': team.create_time.strftime('%Y-%m-%d'),
                    'member_count': team.members.count(),
                    'members': [model_to_dict(student, fields=['id', 'student_id', 'name']) for student in team.members.all()],
                    'businesses': [get_business_detail(stwb.business) for stwb in team.studentwatchingbusiness_set.all()]
                } for team in
                    StudentWatchingTeam.objects.filter(studentwatchingbusiness__course_id=course.id).distinct()]
            } for course in courses]

            paging = {
                'count': paginator.count,
                'has_previous': courses.has_previous(),
                'has_next': courses.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': courses.number,
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
        teachers = request.POST.get("teachers")
        courseCount = request.POST.get("courseCount")
        experienceTime = request.POST.get("experienceTime")

        login_type = request.session['login_type']

        if login_type not in [4, 8, 3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if login_type not in [4, 8]:
            course_type = 0
            tcompany_id = request.user.tcompanymanagers_set.get().tcompany.id
        else:
            course_type = 1
            tcompany_id = request.user.tcompany.id

        course = Course.objects.filter(courseId=courseId).first()
        if course is None:
            course = Course.objects.create(
                courseId=courseId,
                courseName=courseName,
                courseSeqNum=int(courseSeqNum),
                courseSemester=courseSemester,
                courseCount=int(courseCount),
                experienceTime=experienceTime,
                tcompany_id=tcompany_id,
                created_by=request.user,
                type=course_type
            )
        if login_type not in [4, 8]:
            if teachers != "":
                teachers = json.loads(teachers)
                for teacher in teachers:
                    teacherName = teacher['teacher_name']
                    teacherId = teacher['teacher_id']
                    user = Tuser.objects.filter(username=teacherName + '-' + teacherId).first()
                    if not user:
                        user = AllGroups.objects.get(
                            id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.create(
                            username=teacherName + '-' + teacherId,
                            name=teacherName,
                            teacher_id=teacherId,
                            password=make_password('1234567890'),
                            tcompany=request.user.tcompanymanagers_set.get().tcompany,
                            is_review=1,
                        )
                        user.roles.add(TRole.objects.get(id=4))
                    else:
                        user.roles.add(TRole.objects.get(id=4))
                        AllGroups.objects.get(
                            id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.add(user)
                    course.teachers.add(user)

        else:
            user = request.user
            course.teachers.add(user)

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
        teachers = AllGroups.objects.get(
            id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.filter(
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
def api_course_check_attention(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        notificationID = request.GET.get("notificationID")
        universityID = request.GET.get("universityID")
        set = request.GET.get("set")

        ulcs = UniversityLinkedCompany.objects.filter(pk=universityID)
        if not ulcs.first():
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if int(set) == -1:
            ulcs.delete()
        else:
            ulcs.update(
                status=set,
                seted_company_manager=request.user.tcompanymanagers_set.first().id,
                seted_time=datetime.now()
            )
        if TNotifications.objects.get(pk=notificationID) is not None:
            TNotifications.objects.filter(pk=notificationID).delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
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
        teacher1 = request.POST.get("teacher1", None)
        teacher2 = request.POST.get("teacher2", None)
        teacher3 = request.POST.get("teacher3", None)

        tcourse = Course.objects.filter(pk=id).first()
        tcourse.teachers.clear()
        if teacher1:
            tcourse.teachers.add(Tuser.objects.get(pk=teacher1))
        if teacher2:
            tcourse.teachers.add(Tuser.objects.get(pk=teacher2))
        if teacher3:
            tcourse.teachers.add(Tuser.objects.get(pk=teacher3))

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
        if request.session['login_type'] not in [3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        company = request.user.tcompanymanagers_set.get().tcompany if request.session['login_type'] == 3 \
            else request.user.t_company_set_assistants.get()
        companyId = company.id

        excelData = request.POST.get("excelData", None)
        excelData = json.loads(excelData)
        for course in excelData:
            item = course['item'][0]
            courseId = str(item[u'courseId']).encode('utf8')
            courseName = str(item[u'courseName']).encode('utf8')
            courseSeqNum = int(item[u'courseSeqNum'])
            courseSemester = str(item[u'courseSemester']).encode('utf8')
            teachers = [{
                'teacher_name': str(item[u'teacherName1']).encode('utf8'),
                'teacher_id': str(item[u'teacherId1']).encode('utf8')
            }]
            if 'teacherName2' in item and 'teacherId2' in item:
                teachers.append({
                    'teacher_name': str(item[u'teacherName2']).encode('utf8'),
                    'teacher_id': str(item[u'teacherId2']).encode('utf8')
                })
            if 'teacherName3' in item and 'teacherId3' in item:
                teachers.append({
                    'teacher_name': str(item[u'teacherName3']).encode('utf8'),
                    'teacher_id': str(item[u'teacherId3']).encode('utf8')
                })
            courseCount = int(item[u'courseCount'])
            experienceTime = str(item[u'experienceTime']).encode('utf8')

            tcourse = Course.objects.filter(courseId=courseId).first()
            if tcourse is None:
                tcourse = Course.objects.create(
                    courseId=courseId,
                    courseName=courseName,
                    courseSeqNum=int(courseSeqNum),
                    courseSemester=courseSemester,
                    courseCount=int(courseCount),
                    experienceTime=experienceTime,
                    tcompany_id=companyId,
                    created_by=request.user,
                )
            for teacher in teachers:
                teacherName = teacher['teacher_name']
                teacherId = teacher['teacher_id']
                user = Tuser.objects.filter(username=teacherName + '-' + teacherId).first()
                if not user:
                    user = AllGroups.objects.get(id=company.group_id) \
                        .groupInstructors.create(
                        username=teacherName + '-' + teacherId,
                        name=teacherName,
                        teacher_id=teacherId,
                        password=make_password('1234567890'),
                        tcompany=company,
                        is_review=1,
                    )
                    user.roles.add(TRole.objects.get(id=4))
                else:
                    user.roles.add(TRole.objects.get(id=4))
                    AllGroups.objects.get(
                        id=request.user.tcompanymanagers_set.get().tcompany.group_id).groupInstructors.add(user)
                tcourse.teachers.add(user)
            for student in course['item']:
                studentNo = int(student[u'studentNo'])
                studentName = str(student[u'studentName']).encode('utf8')
                studentClassName = str(student[u'studentClassName']).encode('utf8') if student[
                    u'studentClassName'] else None
                if studentClassName:
                    tclass = TClass.objects.filter(name=studentClassName).first()
                    if not tclass:
                        tclass = TClass.objects.create(name=studentClassName)
                else:
                    tclass = None

                newStudent = Tuser.objects.filter(username=str(companyId) + '_' + str(studentNo)).first()
                if not newStudent:
                    newStudent = Tuser(
                        username=str(companyId) + '_' + str(studentNo),
                        name=studentName,
                        student_id=studentNo,
                        class_name=studentClassName,
                        tclass=tclass,
                        password=make_password('123456'),
                        tcompany=company,
                        is_review=1,
                        course_id=tcourse.id
                    )
                    newStudent.save()
                    newStudent.roles.add(TRole.objects.get(id=9))
                else:
                    newStudent.roles.add(TRole.objects.get(id=9))
                tcourse.students.add(newStudent)

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
            qs = UniversityLinkedCompany.objects.filter(university=request.user.tcompanymanagers_set.get().tcompany,
                                                        linked_company__name__icontains=search)
        else:
            qs = UniversityLinkedCompany.objects.filter(university=request.user.tcompanymanagers_set.get().tcompany)
        groupID = request.user.tcompanymanagers_set.get().tcompany.group_id
        clist = [{'value': item.id, 'text': item.name} for item in
                 TCompany.objects.filter(Q(group_id=groupID, is_default=0) & ~Q(companyType__name='学校'))]

        paginator = Paginator(qs, size)

        try:
            flows = paginator.page(page)
        except EmptyPage:
            flows = paginator.page(1)

        results = [{
            'id': flow.id,
            'linked_company': flow.linked_company.name,
            'setter': flow.seted_company_manager.tuser.username if flow.seted_company_manager is not None else '',
            'created_by': flow.created_by.username,
            'create_time': flow.create_time.strftime('%Y-%m-%d'),
            'seted_time': flow.seted_time.strftime('%Y-%m-%d') if flow.seted_time is not None else '',
            'message': flow.message,
            'status': '申请中' if flow.status == 0 else '已关注' if flow.status == 1 else '已拒绝' if flow.status == 2 else '取消申请中' if flow.status == 3 else '取消已拒绝'
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
        if (UniversityLinkedCompany.objects.filter(
            university=request.user.tcompanymanagers_set.get().tcompany,
            linked_company_id=targetCompany).count()) > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'success'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

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

        ulcs = UniversityLinkedCompany.objects.filter(pk__in=ids)
        ulcs.update(status=3)
        for ulc in ulcs:
            newNotification = TNotifications.objects.create(
                type='attentionCancelRequest_' + str(ulc.id),
                content=request.user.tcompanymanagers_set.get().tcompany.name + ' : 取消关注协议',
                link='request-cancel-check',
                role=TRole.objects.get(id=3),
                mode=0
            )

            for userItem in TCompany.objects.get(id=ulc.linked_company_id).tcompanymanagers_set.all():
                newNotification.targets.add(userItem.tuser)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_send_cancel_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
