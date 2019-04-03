#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging

import re
import xlrd
import xlwt

from account.models import TClass
from django.utils.http import urlquote

from django.db.models import Q, Count
from django.http import HttpResponse
from course.models import *
from project.models import Project
from team.models import TeamMember
from utils import code, const, query
from utils.request_auth import auth_check

logger = logging.getLogger(__name__)


# 课程列表
def api_course_list(request):
    try:
        search = request.GET.get("search", None)  # 搜索关键字

        qs = Course.objects.all()

        if search:
            qs = qs.filter(Q(name__icontains=search))

        data = []

        for course in qs:
            projects = Project.objects.filter(course=course.name, del_flag=0)
            if projects and len(projects) > 0:
                data.append({'name': course.name})
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课堂列表
# 三期变更 学生用户在建设实验任务时，选择注册课堂，下拉菜单内容为该小组学生名下共同绑定的课堂信息
def api_course_class_list(request):
    try:
        search = request.GET.get("search", None)  # 搜索关键字
        team_id = request.GET.get("team_id", None)  # 小组id

        sql = '''SELECT DISTINCT a.id, a.no, a.name, a.sort, a.term, d.name teacher1
                from t_course_class a 
                LEFT JOIN t_course_class_student b on a.id = b.course_class_id
                INNER JOIN t_team_member c on b.student_id = c.user_id
                LEFT JOIN t_user d on a.teacher1_id = d.id '''

        where_sql = ''' where a.del_flag = 0 and c.del_flag = 0 '''

        if team_id:
            where_sql += ' and c.team_id = ' + team_id

        if search:
            where_sql += 'a.name like \'%' + search + '%\''

        sql += where_sql

        logger.info(sql)

        qs = query.select(sql, ['id', 'no', 'name', 'sort', 'term', 'teacher1'])

        # 三期 如果有一个学生不在某个课堂中，则不显示这个课堂
        ret_qs = []
        if team_id:
            for course in qs:
                # student_ids = CourseClassStudent.objects.filter(course_class_id=course['id'])
                # .values_list('student_id', flat=True)
                # user_ids = TeamMember.objects.filter(team_id=team_id, del_flag=0).values_list('user_id', flat=True)

                sql1 = '''SELECT student_id from t_course_class_student where course_class_id = %s''' % course['id']
                logger.info(sql1)
                student_ids = query.select(sql1, ['student_id'])

                sql2 = '''SELECT t.id user_id
                        from t_user t LEFT JOIN t_class c ON c.id=t.tclass_id LEFT JOIN t_team_member m ON m.user_id=t.id
                        WHERE m.del_flag=0 and t.del_flag=0 and t.is_active=1 and m.team_id=%s''' % team_id
                logger.info(sql2)
                user_ids = query.select(sql2, ['user_id'])

                # logger.info(','.join(student_ids))
                # logger.info(','.join(user_ids))

                student_arr = []

                for student in student_ids:
                    student_arr.append(student['student_id'])

                flag = True
                for user_id in user_ids:
                    if user_id['user_id'] not in student_arr:
                        flag = False
                if flag:
                    ret_qs.append(course)
                pass
        else:
            ret_qs = qs

        # qs = CourseClass.objects.all()
        #
        # if search:
        #     qs = qs.filter(Q(name__icontains=search))
        #
        # data = []
        #
        # for course in qs:
        #     data.append({'id': course.pk, 'no': course.no, 'name': course.name, 'sort': course.sort,
        #                  'term': course.term, 'teacher1': course.teacher1.name if course.teacher1 else ''})
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = ret_qs
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_class_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 老师的课堂列表
def api_course_list_class_teacher(request):
    try:
        user_id = request.GET.get("user_id", None)  # 老师ID
        search = request.GET.get("search", None)  # 搜索关键字

        qs = CourseClass.objects.filter(Q(teacher1__id=user_id) | Q(teacher2__id=user_id))
        if search:
            qs = qs.filter(Q(name__icontains=search))

        data = []

        for course in qs:
            student_num = CourseClassStudent.objects.filter(course_class=course).aggregate(Count('id'))  # 查询学生人数
            data.append({'id': course.pk, 'no': course.no, 'name': course.name, 'sort': course.sort,
                         'term': course.term, 'time': course.time, 'experiment_time': course.experiment_time,
                         'student_num': student_num['id__count'] if student_num else 0})
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_class_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期课堂学生管理列表
def api_course_student_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        sql = '''SELECT r.id r_id, a.id, a.no c_no, a.name c_name, a.sort c_sort, a.term c_term, b.name t_name, b.username t_username, 
                a.time c_time, a.experiment_time c_experiment_time, e.username s_username, e.name s_name, 
                f.name class_name
                from t_course_class_student r
                LEFT JOIN t_course_class a ON r.course_class_id = a.id
                LEFT JOIN t_user b on a.teacher1_id = b.id 
                LEFT JOIN t_user e on r.student_id = e.id
                LEFT JOIN t_class f on e.tclass_id = f.id'''
        count_sql = '''SELECT count(1) 
                from t_course_class_student r
                LEFT JOIN t_course_class a ON r.course_class_id = a.id
                LEFT JOIN t_user b on a.teacher1_id = b.id 
                LEFT JOIN t_user e on r.student_id = e.id
                LEFT JOIN t_class f on e.tclass_id = f.id'''
        where_sql = ''' where a.del_flag = 0 and e.del_flag = 0'''
        order_by_sql = ''' order by r.id desc'''

        if search:
            where_sql += ' and (a.no like \'%' + search + '%\' or a.`name` like \'%' + search + '%\' ' \
                         'or b.name like \'%' + search + '%\' or b.username like \'%' + search + '%\' ' \
                         'or e.`name` like \'%' + search + '%\' or e.username like \'%' + search + '%\')'

        # 三期 - 加上是否共享字段 并且 只显示本单位数据或者共享数据
        user = request.user
        if request.session['login_type'] != 4:
            where_sql += ' and ((b.tcompany_id = ' + str(user.tcompany_id) + ' and e.tcompany_id = ' + str(user.tcompany_id) \
                        + ') or (b.tcompany_id = ' + str(user.tcompany_id)+' and e.is_share=1)' \
                        + ' or (e.tcompany_id = ' + str(user.tcompany_id)+' and b.is_share=1)' \
                        + ' or (b.is_share = 1 and e.is_share=1))'

        sql += where_sql
        sql += order_by_sql
        count_sql += where_sql
        logger.info(sql)
        data = query.pagination_page(sql, ['r_id', 'id', 'c_no', 'c_name', 'c_sort', 'c_term', 't_name', 't_username',
                                           'c_time', 'c_experiment_time', 's_username', 's_name', 'class_name'],
                                     count_sql, int(page), int(size))
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期课堂学生管理列表导入
def api_course_student_list_import(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        upload_file = request.FILES.get("file", None)  # 文件

        # 解析exl内容
        wb = xlrd.open_workbook(filename=None, file_contents=upload_file.read())
        sheet = wb.sheet_by_index(0)

        # 返回的excel
        report = xlwt.Workbook(encoding='utf8')
        sheet_ret = report.add_sheet(u'sheet1')
        logger.info('name:%s,rows:%s,cols:%s' % (sheet.name, sheet.nrows, sheet.ncols))

        # 返回的excel的表头
        sheet_ret.write(0, 0, '课程号')
        sheet_ret.write(0, 1, '课程名')
        sheet_ret.write(0, 2, '课序号')
        sheet_ret.write(0, 3, '开课学期')
        sheet_ret.write(0, 4, '任课老师')
        sheet_ret.write(0, 5, '工号')
        sheet_ret.write(0, 6, '课时')
        sheet_ret.write(0, 7, '实验学时')
        sheet_ret.write(0, 8, '学号')
        sheet_ret.write(0, 9, '姓名')
        sheet_ret.write(0, 10, '班级')
        sheet_ret.write(0, 11, '导入状态')
        sheet_ret.write(0, 12, '反馈信息')

        # 读取excel每一行的数据
        for i in range(1, sheet.nrows):
            # 课程号， 课程名， 课序号， 开课学期， 任课老师， 工号， 课时， 实验学时， 学号， 姓名， 班级
            flag = True  # 保存是否成功标志
            msg = []  # 错误信息

            # 获取excel数据行
            c0 = sheet.cell(i, 0).value  # 课程号
            if isinstance(c0, float):
                c0 = int(c0)
            c1 = sheet.cell(i, 1).value  # 课程名
            c2 = sheet.cell(i, 2).value  # 课序号
            if isinstance(c0, float):
                c0 = int(c0)
            c3 = sheet.cell(i, 3).value  # 开课学期
            c4 = sheet.cell(i, 4).value  # 任课老师
            c5 = sheet.cell(i, 5).value  # 工号
            if isinstance(c5, float):
                c5 = int(c5)
            c6 = sheet.cell(i, 6).value  # 课时
            c7 = sheet.cell(i, 7).value  # 实验学时
            c8 = sheet.cell(i, 8).value  # 学号
            if isinstance(c8, float):
                c8 = int(c8)
            c9 = sheet.cell(i, 9).value  # 姓名
            c10 = sheet.cell(i, 10).value  # 班级

            # 返回excel数据行
            sheet_ret.write(i, 0, c0)
            sheet_ret.write(i, 1, c1)
            sheet_ret.write(i, 2, c2)
            sheet_ret.write(i, 3, c3)
            sheet_ret.write(i, 4, c4)
            sheet_ret.write(i, 5, c5)
            sheet_ret.write(i, 6, c6)
            sheet_ret.write(i, 7, c7)
            sheet_ret.write(i, 8, c8)
            sheet_ret.write(i, 9, c9)
            sheet_ret.write(i, 10, c10)

            if None in (c0, c3, c5, c8):
                flag = False
                msg.append("错误：课程号列1，开课学期列4， 工号列6，学号列9不允许为空")
            elif not re.match(r"(\d{4}(-)\d{4}(-)[1,2]$)", c3):
                flag = False
                msg.append("错误：开课学期列4格式如下：2017-2018-1 | 2017-2018-2")
            else:

                ref = CourseClassStudent()  # 课堂和学生的关联关系
                course_class = CourseClass()  # 课堂

                # 检查课程号是否存在，
                # *** 判断课程号+课序号+开课学期是否存在，如果存在则可以导入这些存在的课堂的学生信息
                cc = CourseClass.objects.filter(no=c0, sort=c2, term=c3, del_flag=0)

                if cc:  # 已经存在了的课堂，提取查询的值
                    course_class = cc.first()
                    # 如果是已经删除了的课堂， 则将删除状态重置
                    if course_class.del_flag == 1:
                        course_class.del_flag = 0
                        course_class.save()

                    # 根据老师工号设置任课老师
                    teacher = Tuser.objects.filter(username=c5, del_flag=0)
                    if teacher:
                        course_class.teacher1 = teacher.first()  # 设置老师
                        course_class.save()
                    else:
                        flag = False
                        msg.append("警告：根据工号未找到任课老师，列5")

                else:  # 不存在，则创建课堂
                    course_class.no = c0
                    course_class.name = c1
                    course_class.sort = c2
                    course_class.term = c3

                    # 根据老师工号设置任课老师
                    teacher = Tuser.objects.filter(username=c5, del_flag=0)
                    if teacher:
                        course_class.teacher1 = teacher.first()  # 设置老师
                    else:  # 未找到老师依然保存课堂信息
                        flag = False
                        msg.append("警告：根据工号未找到任课老师，列5")

                    if c6 and isinstance(c6, float):
                        course_class.time = int(c6)
                    if c7 and isinstance(c7, float):
                        course_class.experiment_time = int(c7)
                    course_class.save()  # 保存课堂
                    pass

                ref.course_class = course_class  # 设置课堂

                # 根据学号设置学生
                students = Tuser.objects.filter(username=c8, del_flag=0)
                if students:
                    student = students.first()
                    ref.student = student  # 设置学生
                    exist = CourseClassStudent.objects.filter(course_class=course_class, student=student).exists()
                    if not exist:
                        ref.save()  # 保存课堂和学生的关联关系
                    else:
                        flag = False
                        msg.append("该记录已存在")
                else:
                    flag = False
                    msg.append("警告：根据学号未找到学生，列9")

            # 保存用户并写入成功失败的状态和原因
            if flag:
                sheet_ret.write(i, 11, '成功')
            else:
                sheet_ret.write(i, 11, '失败')
            sheet_ret.write(i, 12, '；'.join(msg))

            logger.info('c0:%s,c1:%s,c2:%s,c3:%s,c4:%s' % (c0, c1, c2, c3, c4))
            pass

        # 返回带结果和原因的excel
        # response = HttpResponse(content_type='application/vnd.ms-excel')
        filename = u'课堂信息导入结果反馈'
        # response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
        # report.save(response)
        report.save('media/%s.xls' % filename)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'file': '/media/%s.xls' % filename
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_logout Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 设置样式
def set_style(height, bold=False):
    style = xlwt.XFStyle()  # 初始化样式
    font = xlwt.Font()  # 为样式创建字体
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


# 三期课堂学生管理列表导出
def api_course_student_list_export(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        template = request.GET.get("template", None)  # 是否是模板

        sql = '''SELECT a.no c_no, a.name c_name, a.sort c_sort, a.term c_term, b.name t_name, b.username t_username, 
                a.time c_time, a.experiment_time c_experiment_time, e.username s_username, e.name s_name, 
                f.name class_name
                from t_course_class_student r
                LEFT JOIN t_course_class a ON r.course_class_id = a.id
                LEFT JOIN t_user b on a.teacher1_id = b.id 
                LEFT JOIN t_user e on r.student_id = e.id
                LEFT JOIN t_class f on e.tclass_id = f.id'''
        count_sql = '''SELECT count(1) 
                from t_course_class_student r
                LEFT JOIN t_course_class a ON r.course_class_id = a.id
                LEFT JOIN t_user b on a.teacher1_id = b.id 
                LEFT JOIN t_user e on r.student_id = e.id
                LEFT JOIN t_class f on e.tclass_id = f.id'''
        where_sql = ''' where a.del_flag = 0 and b.del_flag = 0 and e.del_flag = 0'''

        if search:
            where_sql += ' and (a.`name` like \'%' + search + '%\' or b.name like \'%' + search + \
                         '%\' or e.`name` like \'%' + search + '%\')'

        sql += where_sql
        count_sql += where_sql
        sql += ' order by a.create_time desc'

        logger.info(sql)

        if template == '1':
            data = query.pagination_page(sql, ['c_no', 'c_name', 'c_sort', 'c_term', 't_name', 't_username',
                                               'c_time', 'c_experiment_time', 's_username', 's_name', 'class_name'],
                                         count_sql, 1, 2)
        else:
            data = query.pagination_page(sql, ['c_no', 'c_name', 'c_sort', 'c_term', 't_name', 't_username',
                                               'c_time', 'c_experiment_time', 's_username', 's_name', 'class_name'],
                                         count_sql, 1, 50000)

        report = xlwt.Workbook(encoding='utf8')
        sheet = report.add_sheet(u'用户列表')
        title = [u'课程号', u'课程名', u'课序号', u'开课学期', u'任课老师', u'工号', u'课时', u'实验学时', u'学号', u'姓名', u'班级']
        row = 1
        for r in data['results']:
            sheet.write(row, 0, r['c_no'])
            sheet.write(row, 1, r['c_name'])
            sheet.write(row, 2, r['c_sort'])
            sheet.write(row, 3, r['c_term'])
            sheet.write(row, 4, r['t_name'])
            sheet.write(row, 5, r['t_username'])
            sheet.write(row, 6, r['c_time'])
            sheet.write(row, 7, r['c_experiment_time'])
            sheet.write(row, 8, r['s_username'])
            sheet.write(row, 9, r['s_name'])
            sheet.write(row, 10, r['class_name'])
            row += 1
            pass

        # 设置样式
        for i in range(0, len(title)):
            sheet.write(0, i, title[i], set_style(220, True))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        filename = urlquote(u'课堂学生管理列表')
        response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
        report.save(response)
        return response

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期课程删除
def api_course_delete(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        course_id = request.GET.get("course_id", None)  # 课程id
        sql = '''SELECT distinct e.username s_username, e.name s_name, 
                                        f.name class_name
                                    from t_course_class_student r
                                    LEFT JOIN t_course_class a ON r.course_class_id = a.id
                                    LEFT JOIN t_user b on a.teacher1_id = b.id 
                                    LEFT JOIN t_user e on r.student_id = e.id
                                    LEFT JOIN t_class f on e.tclass_id = f.id'''
        where_sql = ''' where a.del_flag = 0 and e.del_flag = 0 '''
        where_sql += ''' and a.id = '''
        where_sql += str(course_id)
        count_sql = '''select count(1) student_num from (''' + sql + where_sql + ''') ttt'''
        logger.info(count_sql)
        # 查询课程的学生人数
        temp_data = query.query_sql(count_sql, ['student_num'])
        student_num = temp_data[0]['student_num']
        if student_num > 0:
            resp = code.get_msg(code.MESSAGE_COURSE_STUDENT_EXISTS)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        CourseClass.objects.filter(id=course_id).delete()
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期课程管理列表
def api_course_list_v3(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        where_sql = ''' where a.del_flag = 0 and b.del_flag = 0 '''

        if search:
            where_sql += ' and (a.no like \'%' + search + '%\' or a.`name` like \'%' + search \
                         + '%\' or b.name like \'%' + search + '%\' or b.username like \'%' + search + '%\')'

        # 三期 - 加上是否共享字段 并且 只显示本单位数据或者共享数据
        user = request.user
        if request.session['login_type'] != 4:
            where_sql += ' and (b.tcompany_id = ' + str(user.tcompany_id) + ' or a.is_share = 1)'

        sql = '''SELECT a.id, a.no c_no, a.name c_name, a.sort c_sort, a.term c_term, b.name t_name, 
                    b.username t_username, a.time c_time, a.experiment_time c_experiment_time, 1 as student_num, 
                    a.is_share
                from t_course_class a 
                LEFT JOIN t_user b on a.teacher1_id = b.id '''
        sql += where_sql
        count_sql = '''SELECT count(1)
                from t_course_class a 
                LEFT JOIN t_user b on a.teacher1_id = b.id '''
        count_sql += where_sql
        sql += ' order by a.create_time desc'
        logger.info(sql)
        data = query.pagination_page(sql, ['id', 'c_no', 'c_name', 'c_sort', 'c_term', 't_name', 't_username',
                                           'c_time', 'c_experiment_time', 'student_num', 'is_share'],
                                     count_sql, int(page), int(size))
        # 查询每个课堂下的学生人数
        for d in data['results']:
            logger.info('=======查询每个课堂下的学生人数=======')
            sql = '''SELECT distinct e.username s_username, e.name s_name, 
                                f.name class_name
                            from t_course_class_student r
                            LEFT JOIN t_course_class a ON r.course_class_id = a.id
                            LEFT JOIN t_user b on a.teacher1_id = b.id 
                            LEFT JOIN t_user e on r.student_id = e.id
                            LEFT JOIN t_class f on e.tclass_id = f.id'''
            where_sql = ''' where a.del_flag = 0 and e.del_flag = 0 '''
            where_sql += ''' and a.id = '''
            where_sql += str(d['id'])
            count_sql = '''select count(1) student_num from (''' + sql + where_sql + ''') ttt'''
            logger.info(count_sql)
            temp_data = query.query_sql(count_sql, ['student_num'])
            student_num = temp_data[0]['student_num']
            logger.info(student_num)
            d['student_num'] = student_num
            pass
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 在课程信息中查看学生信息
def api_course_class_student_v3(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        course_class_id = request.GET.get("course_class_id", None)  # 课程id
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        sql = '''SELECT distinct e.username s_username, e.name s_name, 
                    f.name class_name
                from t_course_class_student r
                LEFT JOIN t_course_class a ON r.course_class_id = a.id
                LEFT JOIN t_user b on a.teacher1_id = b.id 
                LEFT JOIN t_user e on r.student_id = e.id
                LEFT JOIN t_class f on e.tclass_id = f.id'''
        where_sql = ''' where a.del_flag = 0 and e.del_flag = 0'''

        where_sql += ''' and a.id = '''
        where_sql += course_class_id

        if search:
            where_sql += ' and ( e.username like \'%' + search + '%\' or e.`name` like \'%' + search + '%\' )'

        sql += where_sql
        count_sql = '''select count(1) from (''' + sql + ''') ttt'''
        sql += ' order by a.create_time desc'
        logger.info(sql)
        data = query.pagination_page(sql, ['s_username', 's_name', 'class_name'],
                                     count_sql, int(page), int(size))
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课堂信息编辑
def api_course_class_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        course_class_id = request.POST.get("course_class_id", None)  # 课程id
        c_name = request.POST.get("c_name", None)  # 课程名称
        c_term = request.POST.get("c_term", None)  # 开课学期
        c_sort = request.POST.get("c_sort", None)  # 课序号
        c_no = request.POST.get("c_no", None)  # 课程号

        course = CourseClass.objects.get(pk=course_class_id)
        if c_name:
            course.name = c_name
        if c_term:
            course.term = c_term
        if c_sort:
            course.sort = c_sort
        if c_no:
            course.no = c_no

        course.save()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'id': course.pk, 'no': course.no, 'name': course.name, 'sort': course.sort,
                     'term': course.term, 'teacher1': course.teacher1.name}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 课堂学生关联信息删除
def api_course_class_student_delete(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        ids = request.GET.get("ids", None)  # 关联id，用逗号连接

        # 删除关联关系， 根据多个id删除
        id_arr = ids.split(',')
        if None in id_arr or u'' in id_arr:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        for delete_id in id_arr:
            item = CourseClassStudent.objects.get(pk=delete_id)
            item.delete()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期新增课堂学生记录
def api_course_student_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        c_no = request.POST.get("c_no", None)  # 课程号
        c_name = request.POST.get("c_name", None)  # 课程名
        c_sort = request.POST.get("c_sort", None)  # 课序号
        c_term = request.POST.get("c_term", None)  # 开课学期
        t_name = request.POST.get("t_name", None)  # 任课老师
        t_username = request.POST.get("t_username", None)  # 工号
        c_time = int(request.POST.get("c_time", None), 0)  # 课时
        c_experiment_time = int(request.POST.get("c_experiment_time", None), 0)  # 实验学时
        s_username = request.POST.get("s_username", None)  # 学号
        s_name = request.POST.get("s_name", None)  # 姓名
        class_name = request.POST.get("class_name", None)  # 班级

        if None in (c_no, c_name, c_sort, c_term, s_username, c_time, c_experiment_time, ):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 课程是否存在， 如果不存在则创建
        c = CourseClass.objects.filter(no=c_no, sort=c_sort, term=c_term, del_flag=0)
        if c:
            course_class = c.first()
            course_class.del_flag = 0
            course_class.save()
            # 根据老师工号设置任课老师
            teacher = Tuser.objects.filter(username=t_username, del_flag=0)
            if teacher:
                course_class.teacher1 = teacher.first()  # 设置老师
                course_class.save()
            else:
                resp = code.get_msg(code.PARAMETER_ERROR)
                resp['m'] = '根据工号未找到任课老师'
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            pass
        else:
            try:
                c_sort = int(c_sort)
            except Exception as e:
                logger.exception('api_account_users Exception:{0}'.format(str(e)))
                resp = code.get_msg(code.PARAMETER_ERROR)
                resp['m'] = '课序号必须为整数'
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            if not c_name:
                resp = code.get_msg(code.PARAMETER_ERROR)
                resp['m'] = '课程名不能为空'
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            if not c_term:
                resp = code.get_msg(code.PARAMETER_ERROR)
                resp['m'] = '开课学期不能为空'
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            if not re.match(r"(\d{4}(-)\d{4}(-)[1,2]$)", c_term):
                resp = code.get_msg(code.PARAMETER_ERROR)
                resp['m'] = '开课学期列4格式如下：2017-2018-1'
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            course_class = CourseClass()
            course_class.no = c_no
            course_class.name = c_name
            course_class.time = c_time
            course_class.experiment_time = c_experiment_time
            course_class.sort = c_sort
            teachers = Tuser.objects.filter(username=t_username, del_flag=0)
            if teachers:
                course_class.teacher1 = teachers.first()
            else:
                resp = {'c': 3333, 'm': u'老师不存在'}
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            course_class.term = c_term
            course_class.save()

        # 学生用户是否存在
        s = Tuser.objects.filter(username=s_username, del_flag=0)
        if s:
            student = s.first()
            student.del_flag = 0
            student.save()
            pass
        else:
            resp = {'c': 3333, 'm': u'学生不存在'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 保存课堂和学生的关联关系
        cs = CourseClassStudent.objects.filter(course_class_id=course_class.id, student_id=student.id)
        if not cs:
            cs = CourseClassStudent()
            cs.course_class = course_class
            cs.student = student
            cs.save()
        else:
            resp = {'c': 3333, 'm': u'保存的记录已存在'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期 - 共享
def api_course_share(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        data = request.GET.get("data", None)  # id列表json:[1,2,3]
        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        data = json.loads(data)
        ids_set = set(data)
        ids = [i for i in ids_set]
        CourseClass.objects.filter(id__in=ids).update(is_share=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

