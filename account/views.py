#!/usr/bin/python
# -*- coding=utf-8 -*-
import os
import json
import logging

import xlrd
import xlwt
import uuid
from course.models import CourseClassStudent, CourseClass
from group.models import AllGroups
from group.models import TGroupManagerAssistants
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.http import urlquote
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files import File
from django.forms.models import model_to_dict
from account.service import user_info
from account.service import get_client_ip
from django.contrib import auth
from django.http import JsonResponse
from django.http import HttpResponse
from account.models import Tuser, TCompany, TClass, LoginLog, TRole, TCompanyManagerAssistants, TPermission, TAction
from experiment.models import Experiment
from team.models import TeamMember
from utils import code, const, query, easemob, tools, config
from utils.public_fun import loginLog
from utils.request_auth import auth_check
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from random import randint
from datetime import datetime, timedelta
from system.models import UploadFile
from django.core.paginator import Paginator, EmptyPage
from itertools import groupby

logger = logging.getLogger(__name__)


# 用户名查询
def api_account_query(request):
    try:
        username = request.GET.get("username", None)  # 用户名

        user = Tuser.objects.filter(username=username, del_flag=0).first()
        if user:
            # 用户所属的类型列表
            resp = code.get_msg(code.SUCCESS)
            roles = user.roles.all().values_list('id', 'name')
            resp['d'] = {'is_director': user.director, 'is_manage': user.manage, 'is_admin': user.is_admin,
                         'roles': list(roles)}
        else:
            resp = code.get_msg(code.USER_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_query Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户列表
def api_account_users(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        course_id = request.GET.get("course_id", None)  # 课堂id
        user_type = request.GET.get("type", 1)  # 用户类型
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        sql = '''SELECT t.id,t.`name`,t.username,t.nickname,t.type,t.qq,t.gender,c.`name` class_name
        from t_user t LEFT JOIN t_class c ON t.tclass_id=c.id'''
        count_sql = '''SELECT count(1) from t_user t LEFT JOIN t_class c ON t.tclass_id=c.id'''
        where_sql = ' WHERE t.del_flag=0 and t.is_active=1 and t.is_superuser=0'

        if search:
            where_sql += ' and (t.`name` like \'%' + search + '%\' or t.username like \'%' + search + \
                         '%\' or c.`name` like \'%' + search + '%\')'

        # 三期 - 如果存在课堂id，则根据课堂删选用户
        if course_id:
            inner_join_sql = ''' inner join ( select distinct course_class_id, student_id 
            from t_course_class_student ) r on t.id = r.student_id'''
            sql += inner_join_sql
            count_sql += inner_join_sql
            where_sql += ' and r.course_class_id = ' + course_id
            pass

        # if user_type:
        #     where_sql += ' and t.type=%s ' % user_type
        sql += where_sql
        count_sql += where_sql
        sql += ' order by username'
        logger.info(sql)
        data = query.pagination_page(sql, ['id', 'name', 'username', 'nickname', 'type', 'qq', 'gender', 'class_name'],
                                     count_sql, int(page), int(size))
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户退出
def api_account_logout(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        auth.logout(request)
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_logout Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def logout_all(user):
    session_obj_list = Session.objects.filter(expire_date__gt=timezone.now())
    for session_obj in session_obj_list:
        user_id = session_obj.get_decoded().get("_auth_user_id")
        # logger.info(type(user_id))
        if user_id:
            if int(user_id) == user.pk:
                session_obj.delete()


# 用户登录
def api_account_login(request):
    try:
        username = request.POST.get("username", None)  # 用户名
        password = request.POST.get("password", None)  # 密码
        login_type = int(request.POST.get("login_type", 1))  # 登录身份

        # 参数验证
        if username is None or password is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
        else:
            user_temp = Tuser.objects.filter(username=username, del_flag=0).first()
            if not user_temp:
                resp = code.get_msg(code.USER_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            user = auth.authenticate(username=username, password=password)
            if user:
                if login_type in [5, 9] and user.is_review == 0:
                    resp = code.get_msg(code.USER_NOT_REVIEWED)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                elif login_type in [5, 9] and user.is_review == 2:
                    resp = code.get_msg(code.USER_REVIEWED_FAILED)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # todo 登出相同账号其它登录用户
                logout_all(user)
                try:
                    role = user.roles.get(pk=login_type)
                    auth.login(request, user)
                    # 三期 保存用户的登录类型， 后面有用, 无力吐槽
                    request.session['login_type'] = role.id
                    resp = code.get_msg(code.SUCCESS)
                    resp['d'] = user_info(user.id)
                    resp['d']['identity'] = role.id
                    resp['d']['defaultGroup'] = (
                        Tuser.objects.get(id=user.id).allgroups_set.get().default == 1) if role.id == 2 else False
                    resp['d']['role'] = role.id
                    resp['d']['role_name'] = role.name
                    resp['d']['manage'] = user.manage
                    resp['d']['admin'] = user.is_admin
                    resp['d']['company_id'] = user.tcompany.id if user.tcompany else ''
                    resp['d']['company_name'] = user.tcompany.name if user.tcompany else ''
                    resp['d']['director'] = user.director
                    resp['d']['last_experiment_id'] = user.last_experiment_id
                    manager_info = {}
                    allowedPermissions = []
                    if login_type == 2:
                        group = user.allgroups_set.get()
                        manager_info = {
                            'group_id': group.id
                        }
                    elif login_type == 6:
                        group = user.allgroups_set_assistants.get()
                        assistant_relation = TGroupManagerAssistants.objects.get(all_groups=group, tuser=user)
                        allowedActions = list(assistant_relation.actions.all().values())
                        allowedPermissions = {TPermission.objects.get(pk=k).codename: [x for x in v] for k, v in
                                              groupby(allowedActions, key=lambda x: x['permission_id'])}
                        manager_info = {
                            'group_id': group.id
                        }
                    elif login_type == 3:
                        manager_info = {
                            'company_id': user.tcompanymanagers_set.get().tcompany.id
                        }
                    elif login_type == 7:
                        company = user.t_company_set_assistants.get()
                        assistant_relation = TCompanyManagerAssistants.objects.get(tcompany=company, tuser=user)
                        allowedActions = list(assistant_relation.actions.all().values())
                        allowedPermissions = [{TPermission.objects.get(pk=k).codename: [x for x in v]} for k, v in
                                              groupby(allowedActions, key=lambda x: x['permission_id'])]
                        manager_info = {
                            'company_id': user.t_company_set_assistants.get().id
                        }
                    resp['d']['manager_info'] = manager_info
                    resp['d']['allowed_permissions'] = allowedPermissions
                    if user.last_experiment_id:
                        last_exp = Experiment.objects.get(pk=user.last_experiment_id)
                    else:
                        last_exp = Experiment()
                    resp['d']['last_experiment_status'] = last_exp.status
                    resp['d']['last_experiment_name'] = last_exp.name
                    loginLog(loginType=login_type, userID=user.id, ip=get_client_ip(request))
                except ObjectDoesNotExist:
                    resp = code.get_msg(code.PERMISSION_DENIED)
            else:
                resp = code.get_msg(code.USERNAME_OR_PASSWORD_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_login Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户列表-三期
def api_account_users_v3(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        identity = request.GET.get("identity", 1)  # 管理员类型，实验人员类型类型
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数
        user = request.user

        sql = '''SELECT t.id,t.username,t.name,c.name class_name,d.name company_name,t.gender,t.qq,t.nickname,t.phone,t.email,
                    t.director,t.manage,e.name assigned_by, t.is_share
                    from t_user t 
                    LEFT JOIN t_class c ON t.tclass_id=c.id
                    LEFT JOIN t_company d ON t.tcompany_id=d.id
                    LEFT JOIN t_user e on t.assigned_by = e.id'''
        count_sql = '''SELECT count(1) from t_user t 
                    LEFT JOIN t_class c ON t.tclass_id=c.id
                    LEFT JOIN t_company d ON t.tcompany_id=d.id
                    LEFT JOIN t_user e on t.assigned_by = e.id'''
        where_sql = ' WHERE t.del_flag=0 and t.is_active=1 '  # and t.is_superuser=0'

        if search:
            where_sql += ' and (t.`name` like \'%' + search + '%\' or t.username like \'%' + search + '%\')'

        if identity:
            where_sql += ' and t.identity=%s ' % identity

        # if not user.is_admin:
        #     where_sql += ' and t.tcompany_id=%s ' % user.tcompany_id

        # 三期 - 加上是否共享字段 并且 只显示本单位数据或者共享数据
        if request.session['login_type'] != 4:
            where_sql += ' and (t.tcompany_id = ' + str(user.tcompany_id) + ' or t.is_share = 1)'

        sql += where_sql
        count_sql += where_sql
        sql += ' order by t.update_time desc'
        logger.info(sql)
        data = query.pagination_page(sql, ['id', 'username', 'name', 'class_name', 'company_name', 'gender', 'qq',
                                           'nickname', 'phone', 'email', 'director', 'manage', 'assigned_by',
                                           'is_share'],
                                     count_sql, int(page), int(size))
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询单位列表
def api_account_companys(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        companys = TCompany.objects.all().order_by("-update_time")
        data = [{'id': i.id, 'name': i.name} for i in companys]
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_companys Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询班级列表
def api_account_classes(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        classes = TClass.objects.all().order_by("-update_time")
        data = [{'id': i.id, 'name': i.name} for i in classes]
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_classes Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_account_send_verify_code(request):
    try:
        if ('veification_code' in request.session):
            del request.session['veification_code']
        if ('veification_session_start_time' in request.session):
            del request.session['veification_session_start_time']
        if ('verification_phone' in request.session):
            del request.session['verification_phone']

        to = request.POST.get('to', None)
        if to is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        client = AcsClient(config.ALIYUN_CONFIG['accessKeyId'], config.ALIYUN_CONFIG['accessKeySecret'], 'default')
        message = randint(0, 10 ** 6)
        message = '{:06}'.format(message)
        crequest = CommonRequest()
        crequest.set_accept_format('json')
        crequest.set_domain('dysmsapi.aliyuncs.com')
        crequest.set_method('POST')
        crequest.set_protocol_type('https')
        crequest.set_version('2017-05-25')
        crequest.set_action_name('SendSms')
        crequest.add_query_param('PhoneNumbers', to)
        crequest.add_query_param('SignName', '图灵海际')
        crequest.add_query_param('TemplateParam', '{\"code\":\"' + message + '\"}')
        crequest.add_query_param('TemplateCode', config.ALIYUN_CONFIG['templateCode'])
        response = client.do_action(crequest)
        response = json.loads(response)
        if (response["Message"] == u"OK"):
            request.session['verification_code'] = message
            verification_session_start_time = str(datetime.now())
            request.session['verification_session_start_time'] = verification_session_start_time
            request.session['verification_phone'] = to
            resp = code.get_msg(code.SUCCESS)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_account_password_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_account_password_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        user_id = request.POST.get('id', None)  # 账号
        old_password = request.POST.get('old', None)  # 账号
        new_password = request.POST.get('new', None)  # 密码
        new_password_confirm = request.POST.get('new_confirm', None)  # 密码
        verification_code = request.POST.get('verification_code', None)
        login_type = int(request.POST.get("login_type", 1))  # 登录身份

        user = Tuser.objects.get(pk=user_id)
        role = user.roles.get(pk=login_type)
        if new_password != new_password_confirm or not user.check_password(old_password):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        try:
            print request.session['verification_code']
            if (verification_code is None) or (
                            datetime.now() - datetime.strptime(request.session['verification_session_start_time'],
                                                               "%Y-%m-%d %H:%M:%S.%f") > timedelta(0, 5 * 60, 0)) or (
                        verification_code != request.session['verification_code']):
                resp = code.get_msg(code.PHONE_NOT_VERIFIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        except KeyError as e:
            resp = code.get_msg(code.PHONE_NOT_VERIFIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        user.set_password(new_password)
        user.save()

        logout_all(user)
        auth.login(request, user)
        # 三期 保存用户的登录类型， 后面有用, 无力吐槽
        request.session['login_type'] = role.id
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_account_password_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户更新
def api_account_user_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user_id = request.POST.get('id', None)  # 账号
        username = request.POST.get('username', None)  # 账号
        password = request.POST.get('password', None)  # 密码
        ip = get_client_ip(request)
        nickname = request.POST.get('nickname', None)  # 昵称
        gender = request.POST.get('gender', None)  # 性别
        name = request.POST.get('name', None)  # 姓名
        email = request.POST.get('email', None)  # 邮箱
        phone = request.POST.get('phone', None)  # 联系方式
        qq = request.POST.get('qq', None)  # qq
        identity = request.POST.get('identity', None)  # 身份
        type = request.POST.get('type', None)  # 类型
        class_id = request.POST.get('class_id', None)  # 班级id
        company_id = request.POST.get('company_id', None)  # 所在单位
        director = request.POST.get('director', None)  # 是否具有指导权限
        manage = request.POST.get('manage', None)  # 是否具有管理权限
        verification_code = request.POST.get('verification_code', None)

        user = Tuser.objects.get(pk=user_id)
        user.assigned_by = request.user.id
        if username:
            user.username = username
        if password:
            user.set_password(password)
        if nickname:
            user.nickname = nickname
        if gender:
            user.gender = gender
        if name:
            user.name = name
        if email:
            user.email = email
        if phone:
            user.phone = phone
        if qq:
            user.qq = qq
        if ip:
            user.ip = ip
        if identity:
            user.identity = identity
        if type:
            user.type = type
        if class_id:
            user.tclass_id = class_id
        if company_id:
            user.tcompany_id = company_id
        if director and 'TRUE' == director.upper():
            user.director = True
        else:
            user.director = False
        if manage and 'TRUE' == manage.upper():
            user.manage = True
        else:
            user.manage = False

        try:
            print request.session['verification_code']
            if (verification_code is None) or (
                            datetime.now() - datetime.strptime(request.session['verification_session_start_time'],
                                                               "%Y-%m-%d %H:%M:%S.%f") > timedelta(0, 5 * 60, 0)) or (
                        verification_code != request.session['verification_code']) or (
                        phone != request.session['verification_phone']):
                resp = code.get_msg(code.PHONE_NOT_VERIFIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        except KeyError as e:
            resp = code.get_msg(code.PHONE_NOT_VERIFIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if ('veification_code' in request.session):
            del request.session['veification_code']
        if ('veification_session_start_time' in request.session):
            del request.session['veification_session_start_time']
        if ('verification_phone' in request.session):
            del request.session['verification_phone']
        user.save()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_user_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_account_avatar_img_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user_id = request.GET.get('id', None)  # 账号
        avatar = request.FILES['img']
        filename = str(uuid.uuid4()) + '.png'
        user = Tuser.objects.get(pk=user_id)
        default_storage.delete(user.avatar.name)
        user.avatar.save(filename, avatar, True)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'avatar_path': user.avatar.url
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_account_avatar_img_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 上传文件
def api_account_avatar_img_upload(request):
    try:
        upload_file = request.FILES.get("img", None)  # 文件

        if upload_file:
            obj = UploadFile.objects.create(filename=upload_file.name, file=upload_file)

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': obj.id, 'filename': obj.filename, 'url': obj.file.url, 'md5sum': obj.md5sum,
                'create_time': obj.create_time.strftime('%Y-%m-%d')
            }
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
    except Exception as e:
        logger.exception('api_account_avatar_img_upload Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_get_default_group(request):
    try:
        defaultGroup = AllGroups.objects.get(default=1)
        companies = defaultGroup.tcompany_set.filter(is_default=0)
        defaultGroup = model_to_dict(defaultGroup, fields=['id', 'name'])
        defaultGroup['companies'] = [{'id': i.id, 'name': i.name} for i in companies]
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = defaultGroup
    except Exception as e:
        logger.exception('api_account_user_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# create new user
def api_account_user_create(request):
    try:
        username = request.POST.get('username', None)  # 账号
        name = request.POST.get('name', None)  # 姓名
        password = request.POST.get('password', None)  # 密码
        passwordConfirmation = request.POST.get('passwordConfirmation', None)  # 昵称
        phone = request.POST.get('phone', None)  # 联系方式
        email = request.POST.get('email', None)  # 邮箱
        defaultGroup = AllGroups.objects.get(default=1)
        company = defaultGroup.tcompany_set.get(is_default=1)
        company_id = request.POST.get('company_id', None)  # 所在单位
        company_id = company_id if company_id is not u'' else company.id
        avatar_id = request.POST.get('avatar_id', None)  # 所在单位
        verification_code = request.POST.get('verificationCode', None)

        if password != passwordConfirmation:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        users = Tuser.objects.filter(username=username, del_flag=0)
        if users:
            resp = code.get_msg(code.USER_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        try:
            print request.session['verification_code']
            if (verification_code is None) or (
                            datetime.now() - datetime.strptime(request.session['verification_session_start_time'],
                                                               "%Y-%m-%d %H:%M:%S.%f") > timedelta(0, 5 * 60, 0)) or (
                        verification_code != request.session['verification_code']) or (
                        phone != request.session['verification_phone']):
                resp = code.get_msg(code.PHONE_NOT_VERIFIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        except KeyError as e:
            resp = code.get_msg(code.PHONE_NOT_VERIFIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if ('veification_code' in request.session):
            del request.session['veification_code']
        if ('veification_session_start_time' in request.session):
            del request.session['veification_session_start_time']
        if ('verification_phone' in request.session):
            del request.session['verification_phone']

        user = Tuser(username=username,
                     email=email,
                     name=name,
                     phone=phone,
                     tcompany_id=company_id)
        user.save()
        user.roles.add(TRole.objects.get(id=5))
        user.set_password(password)
        user.save()

        if avatar_id:
            uploadFile = UploadFile.objects.get(pk=avatar_id)
            avatar = uploadFile.file
            filename = str(uuid.uuid4()) + '.png'
            user.avatar = File(avatar, filename)
            user.save()
            avatar.close()
            uploadFile.delete()

        resp = code.get_msg(code.SUCCESS)

    except Exception as e:
        logger.exception('api_account_user_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户保存
def api_account_user_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        username = request.POST.get('username', None)  # 账号
        password = request.POST.get('password', None)  # 密码
        nickname = request.POST.get('nickname', None)  # 昵称
        gender = request.POST.get('gender', None)  # 性别
        name = request.POST.get('name', None)  # 姓名
        email = request.POST.get('email', None)  # 邮箱
        phone = request.POST.get('phone', None)  # 联系方式
        qq = request.POST.get('qq', None)  # qq
        identity = request.POST.get('identity', None)  # 身份
        type = request.POST.get('type', None)  # 类型
        class_id = request.POST.get('class_id', None)  # 班级
        company_id = request.POST.get('company_id', None)  # 所在单位
        director = request.POST.get('director', None)  # 是否具有指导权限
        manage = request.POST.get('manage', None)  # 是否具有管理权限

        users = Tuser.objects.filter(username=username, del_flag=0)
        user = Tuser()
        if users:  # 如果用户时系统中有的， 恢复正常然后更新, md, 这都是什么鬼
            resp = code.get_msg(code.SYSTEM_ERROR)
            resp['m'] = '账户已存在'
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            users = Tuser.objects.filter(username=username)
            if users:  # 如果用户时系统中有的， 恢复正常然后更新, md, 这都是什么鬼
                user = users.first()
                user.del_flag = 0
        user.assigned_by = request.user.id
        user.is_active = 1
        if username:
            user.username = username
            # u = Tuser.objects.filter(username=username, del_flag=0)
            # if u:
            #     resp = code.get_msg(code.USER_EXIST)
            #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if password:
            user.set_password(password)
        if nickname:
            user.nickname = nickname
        if gender:
            user.gender = gender
        if name:
            user.name = name
        if email:
            user.email = email
        if phone:
            user.phone = phone
        if qq:
            user.qq = qq
        if identity:
            user.identity = identity
        if type:
            user.type = type
        if class_id:
            user.tclass_id = class_id
        if company_id:
            user.tcompany_id = company_id
        if director and 'TRUE' == director.upper():
            user.director = True
        else:
            user.director = False
        if manage and 'TRUE' == manage.upper():
            user.manage = True
        else:
            user.manage = False

        user.save()
        easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_logout Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 根据id查询用户信息
def api_account_get_user(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        user_id = request.GET.get('id', None)
        user = Tuser.objects.get(id=user_id)
        assigned_by = None
        if user.assigned_by:
            assigned_by = Tuser.objects.get(id=user.assigned_by)
        data = {'id': user.id, 'username': user.username, 'nickname': user.nickname, 'gender': user.gender,
                'name': user.name, 'email': user.email, 'phone': user.phone, 'qq': user.qq,
                'identity': user.identity, 'type': user.type, 'ip': user.ip, 'is_active': user.is_active,
                'is_admin': user.is_admin, 'class_id': user.tclass.id if user.tclass else '',
                'company_id': user.tcompany.id if user.tcompany else '',
                'director': user.director,
                'manage': user.manage, 'assigned_by': assigned_by.name if assigned_by else '', }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_logout Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 导入用户列表
def api_account_import(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        identity = int(request.POST.get("identity", 1))  # 管理员类型，实验人员类型类型
        logger.info('----------------------')
        logger.info(identity)
        upload_file = request.FILES.get("file", None)  # 文件

        if identity is None or upload_file is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 解析exl内容，生成docx文件，保存数据库。
        wb = xlrd.open_workbook(filename=None, file_contents=upload_file.read())
        sheet = wb.sheet_by_index(0)

        # 返回的excel
        report = xlwt.Workbook(encoding='utf8')
        sheet_ret = report.add_sheet(u'sheet1')
        logger.info('name:%s,rows:%s,cols:%s' % (sheet.name, sheet.nrows, sheet.ncols))
        if identity == 1:  # 实验人员
            # 返回的excel的表头
            sheet_ret.write(0, 0, 'ID')
            sheet_ret.write(0, 1, '姓名')
            sheet_ret.write(0, 2, '班级')
            sheet_ret.write(0, 3, '所在单位')
            sheet_ret.write(0, 4, '性别')
            sheet_ret.write(0, 5, '指导权限')
            sheet_ret.write(0, 6, '管理权限')
            sheet_ret.write(0, 7, '权限分配责任人')
            sheet_ret.write(0, 8, '导入状态')
            sheet_ret.write(0, 9, '反馈信息')
            # u'ID', u'姓名', u'班级', u'所在单位', u'性别', u'指导权限', u'管理权限', u'权限分配责任人'
            # 读取excel每一行的数据
            for i in range(1, sheet.nrows):
                user = Tuser()  # 构造用户对象
                user.identity = identity
                user.set_password(const.PASSWORD_DEFAULT)
                user.is_active = 1
                flag = True  # 保存是否成功标志
                msg = []  # 错误信息

                # 获取excel数据行
                c0 = sheet.cell(i, 0).value
                if isinstance(c0, float):
                    c0 = int(c0)
                c1 = sheet.cell(i, 1).value
                c2 = sheet.cell(i, 2).value
                c3 = sheet.cell(i, 3).value
                c4 = sheet.cell(i, 4).value
                c5 = sheet.cell(i, 5).value
                c6 = sheet.cell(i, 6).value
                c7 = sheet.cell(i, 7).value

                # 返回excel数据行
                sheet_ret.write(i, 0, c0)
                sheet_ret.write(i, 1, c1)
                sheet_ret.write(i, 2, c2)
                # sheet_ret.write(i, 3, c3)
                sheet_ret.write(i, 4, c4)
                # sheet_ret.write(i, 5, c5)
                # sheet_ret.write(i, 6, c6)
                # sheet_ret.write(i, 7, request.user.name)

                if None in (c0,):
                    flag = False
                    msg.append("错误：账号列1不允许为空")
                else:

                    # 检查账号是否为数字
                    if isinstance(c0, float):
                        c0 = int(c0)

                    # 检查账号是否存在
                    users = Tuser.objects.filter(username=c0, del_flag=0)
                    if users:
                        flag = False
                        msg.append('错误：(账户)已存在，（列1)')
                    else:
                        users = Tuser.objects.filter(username=c0)
                        if users:  # 如果用户时系统中有的， 恢复正常然后更新, md, 这都是什么鬼
                            user = users.first()
                            user.del_flag = 0
                            user.identity = identity
                        user.username = c0
                    if None in (c1,):
                        flag = False
                        msg.append('错误：姓名列2不允许为空')
                    elif isinstance(c1, float):
                        flag = False
                        msg.append('错误：姓名列2不允许为数字(认真点好吗？谁家的名字是数字的)')
                    else:
                        # 姓名
                        user.name = c1

                    # 根据班级名称设置班级
                    tclass = TClass.objects.filter(name=c2)
                    if tclass:
                        user.tclass = tclass.first()
                    else:
                        # msg.append('警告：(班级)有误，（列3)')
                        pass

                    # 设置单位
                    # tcompany = TCompany.objects.filter(name=c3)
                    # if tcompany:
                    #     user.tcompany = tcompany.first()
                    # else:
                    #     msg.append('警告：(单位)有误，（列4)')
                    user.tcompany_id = request.user.tcompany_id
                    sheet_ret.write(i, 3, request.user.tcompany.name if request.user.tcompany else '')

                    # 设置性别
                    user.gender = 1 if '男' == c4 else 2
                    # 指导权限
                    # user.director = True if '是' == c5 else False
                    user.director = False
                    sheet_ret.write(i, 5, '否')
                    # 管理权限
                    # user.manage = True if '是' == c6 else False
                    user.manage = False
                    sheet_ret.write(i, 6, '否')

                    # 权限分配责任人
                    # assigned_by = Tuser.objects.filter(name=c7)
                    # if assigned_by:
                    #     user.assigned_by = assigned_by.first().id
                    # else:
                    #     msg.append('警告：(权限分配责任人)有误，（列8)')
                    user.assigned_by = request.user.id
                    sheet_ret.write(i, 7, request.user.name)

                # 保存用户并写入成功失败的状态和原因
                if flag:
                    user.save()
                    easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
                    sheet_ret.write(i, 8, '成功')
                else:
                    sheet_ret.write(i, 8, '失败')
                sheet_ret.write(i, 9, '；'.join(msg))

                logger.info('c0:%s,c1:%s,c2:%s,c3:%s,c4:%s,c5:%s,c6:%s,c7:%s' % (c0, c1, c2, c3, c4, c5, c6, c7))
            pass

        if identity == 2:  # 实验指导
            # 返回的excel的表头
            sheet_ret.write(0, 0, 'ID')
            sheet_ret.write(0, 1, '姓名')
            sheet_ret.write(0, 2, '姓别')
            sheet_ret.write(0, 3, 'QQ')
            sheet_ret.write(0, 4, '昵称')
            sheet_ret.write(0, 5, '所在单位')
            sheet_ret.write(0, 6, '电话')
            sheet_ret.write(0, 7, '邮箱')
            sheet_ret.write(0, 8, '指导权限')
            sheet_ret.write(0, 9, '管理权限')
            sheet_ret.write(0, 10, '权限分配责任人')
            sheet_ret.write(0, 11, '导入状态')
            sheet_ret.write(0, 12, '反馈信息')
            # u'ID', u'姓名', u'姓别', u'QQ', u'昵称', u'所在单位', u'电话', u'邮箱', u'指导权限',
            # u'管理权限', u'权限分配责任人'
            for i in range(1, sheet.nrows):
                user = Tuser()  # 构造用户对象
                user.identity = identity
                user.set_password(const.PASSWORD_DEFAULT)
                user.is_active = 1
                flag = True  # 保存是否成功标志
                msg = []  # 错误信息

                # 获取excel数据行
                c0 = sheet.cell(i, 0).value
                if isinstance(c0, float):
                    c0 = int(c0)
                c1 = sheet.cell(i, 1).value
                c2 = sheet.cell(i, 2).value
                c3 = sheet.cell(i, 3).value
                if isinstance(c3, float):
                    c3 = int(c3)
                c4 = sheet.cell(i, 4).value
                c5 = sheet.cell(i, 5).value
                c6 = sheet.cell(i, 6).value
                if isinstance(c6, float):
                    c6 = int(c6)
                c7 = sheet.cell(i, 7).value
                c8 = sheet.cell(i, 8).value
                c9 = sheet.cell(i, 9).value
                c10 = sheet.cell(i, 10).value

                # 返回excel数据行
                sheet_ret.write(i, 0, c0)
                sheet_ret.write(i, 1, c1)
                sheet_ret.write(i, 2, c2)
                # sheet_ret.write(i, 3, c3)
                sheet_ret.write(i, 4, c4)
                # sheet_ret.write(i, 5, c5)
                # sheet_ret.write(i, 6, c6)
                sheet_ret.write(i, 7, c7)
                # sheet_ret.write(i, 8, c8)
                # sheet_ret.write(i, 9, c9)
                # sheet_ret.write(i, 10, request.user.name)

                if None in (c0,):
                    flag = False
                    msg.append("错误：账号列1不允许为空")
                else:

                    # 检查账号是否为数字
                    if isinstance(c0, float):
                        c0 = int(c0)

                    # 检查账号是否存在
                    users = Tuser.objects.filter(username=c0, del_flag=0)
                    if users:
                        flag = False
                        msg.append('错误：(账户)已存在，（列1)')
                    else:
                        users = Tuser.objects.filter(username=c0)
                        if users:  # 如果用户时系统中有的， 恢复正常然后更新, md, 这都是什么鬼
                            user = users.first()
                            user.del_flag = 0
                            user.identity = identity
                        user.username = c0
                    # 姓名
                    if None in (c1,):
                        flag = False
                        msg.append('错误：姓名列2不允许为空')
                    elif isinstance(c1, float):
                        flag = False
                        msg.append('错误：姓名列2不允许为数字(认真点好吗？谁家的名字是数字的)')
                    else:
                        # 姓名
                        user.name = c1

                    # 设置性别
                    user.gender = 1 if '男' == c2 else 2
                    # QQ
                    user.qq = c3
                    sheet_ret.write(i, 3, str(c3))
                    # 昵称
                    if isinstance(c4, float):
                        flag = False
                        msg.append('错误：昵称列5不允许为数字')
                    else:
                        user.nickname = c4

                    # 设置单位
                    # tcompany = TCompany.objects.filter(name=c5)
                    # if tcompany:
                    #     user.tcompany = tcompany.first()
                    # else:
                    #     msg.append('警告：(单位)有误，（列6)')
                    user.tcompany_id = request.user.tcompany_id
                    sheet_ret.write(i, 5, request.user.tcompany.name if request.user.tcompany else '')

                    # 电话
                    user.phone = c6
                    sheet_ret.write(i, 6, str(c6))
                    # 邮箱
                    user.email = c7

                    # 指导权限, 实验指导都具有指导权限
                    user.director = True
                    sheet_ret.write(i, 8, '否')
                    # 管理权限
                    # user.manage = True if '是' == c9 else False
                    user.manage = False
                    sheet_ret.write(i, 9, '否')

                    # 权限分配责任人
                    # assigned_by = Tuser.objects.filter(name=c10)
                    # if assigned_by:
                    #     user.assigned_by = assigned_by.first().id
                    # else:
                    #     msg.append('警告：(权限分配责任人)有误，（列11)')
                    user.assigned_by = request.user.id
                    sheet_ret.write(i, 10, request.user.name)

                # 保存用户并写入成功失败的状态和原因
                if flag:
                    user.save()
                    easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
                    sheet_ret.write(i, 11, '成功')
                else:
                    sheet_ret.write(i, 11, '失败')
                sheet_ret.write(i, 12, '；'.join(msg))

                logger.info('c0:%s,c1:%s,c2:%s,c3:%s,c4:%s' % (c0, c1, c2, c3, c4))
            pass

        if identity == 3:  # 系统管理员
            # 返回的excel的表头
            sheet_ret.write(0, 0, 'ID')
            sheet_ret.write(0, 1, '姓名')
            sheet_ret.write(0, 2, '姓别')
            sheet_ret.write(0, 3, 'QQ')
            sheet_ret.write(0, 4, '昵称')
            sheet_ret.write(0, 5, '所在单位')
            sheet_ret.write(0, 6, '电话')

            sheet_ret.write(0, 7, '邮箱')
            sheet_ret.write(0, 8, '管理权限')
            sheet_ret.write(0, 9, '权限分配责任人')
            sheet_ret.write(0, 10, '导入状态')
            sheet_ret.write(0, 11, '反馈信息')
            # u'ID', u'姓名', u'姓别', u'QQ', u'昵称', u'所在单位', u'电话', u'邮箱', u'管理权限', u'权限分配责任人'
            for i in range(1, sheet.nrows):
                user = Tuser()  # 构造用户对象
                user.identity = identity
                user.set_password(const.PASSWORD_DEFAULT)
                user.is_active = 1
                flag = True  # 保存是否成功标志
                msg = []  # 错误信息

                # 获取excel数据行
                c0 = sheet.cell(i, 0).value
                if isinstance(c0, float):
                    c0 = int(c0)
                c1 = sheet.cell(i, 1).value
                c2 = sheet.cell(i, 2).value
                c3 = sheet.cell(i, 3).value
                if isinstance(c3, float):
                    c3 = int(c3)
                c4 = sheet.cell(i, 4).value
                c5 = sheet.cell(i, 5).value
                c6 = sheet.cell(i, 6).value
                if isinstance(c6, float):
                    c6 = int(c6)
                c7 = sheet.cell(i, 7).value
                c8 = sheet.cell(i, 8).value
                c9 = sheet.cell(i, 9).value

                # 返回excel数据行
                sheet_ret.write(i, 0, c0)
                sheet_ret.write(i, 1, c1)
                sheet_ret.write(i, 2, c2)
                # sheet_ret.write(i, 3, c3)
                sheet_ret.write(i, 4, c4)
                # sheet_ret.write(i, 5, c5)
                # sheet_ret.write(i, 6, c6)
                sheet_ret.write(i, 7, c7)
                # sheet_ret.write(i, 8, c8)
                # sheet_ret.write(i, 9, request.user.name)

                if None in (c0,):
                    flag = False
                    msg.append("错误：账号列1不允许为空")
                else:

                    # 检查账号是否为数字
                    if isinstance(c0, float):
                        c0 = int(c0)

                    # 检查账号是否存在
                    users = Tuser.objects.filter(username=c0, del_flag=0)
                    if users:
                        flag = False
                        msg.append('错误：(账户)已存在，（列1)')
                    else:
                        users = Tuser.objects.filter(username=c0)
                        if users:  # 如果用户时系统中有的， 恢复正常然后更新, md, 这都是什么鬼
                            user = users.first()
                            user.del_flag = 0
                            user.identity = identity
                        user.username = c0
                    # 姓名
                    if None in (c1,):
                        flag = False
                        msg.append('错误：姓名列2不允许为空')
                    elif isinstance(c1, float):
                        flag = False
                        msg.append('错误：姓名列2不允许为数字(认真点好吗？谁家的名字是数字的)')
                    else:
                        # 姓名
                        user.name = c1

                    # 设置性别
                    user.gender = 1 if '男' == c2 else 2
                    # QQ
                    user.qq = c3
                    sheet_ret.write(i, 3, str(c3))
                    # 昵称
                    user.nickname = c4

                    # 设置单位
                    # tcompany = TCompany.objects.filter(name=c5)
                    # if tcompany:
                    #     user.tcompany = tcompany.first()
                    # else:
                    #     msg.append('警告：(单位)有误，（列6)')
                    user.tcompany_id = request.user.tcompany_id
                    sheet_ret.write(i, 5, request.user.tcompany.name if request.user.tcompany else '')

                    # 电话
                    user.phone = c6
                    sheet_ret.write(i, 6, str(c6))
                    # 邮箱
                    user.email = c7

                    # 指导权限, 系统管理员都具有指导权限
                    user.director = True
                    # 管理权限, 系统管理员都具有管理权限
                    user.manage = True
                    sheet_ret.write(i, 8, '否')

                    # 权限分配责任人
                    # assigned_by = Tuser.objects.filter(name=c9)
                    # if assigned_by:
                    #     user.assigned_by = assigned_by.first().id
                    # else:
                    #     msg.append('警告：(权限分配责任人)有误，（列11)')
                    user.assigned_by = request.user.id
                    sheet_ret.write(i, 9, request.user.name)

                # 保存用户并写入成功失败的状态和原因
                if flag:
                    user.save()
                    easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
                    sheet_ret.write(i, 10, '成功')
                else:
                    sheet_ret.write(i, 10, '失败')
                sheet_ret.write(i, 11, '；'.join(msg))

                logger.info('c0:%s,c1:%s,c2:%s,c3:%s,c4:%s' % (c0, c1, c2, c3, c4))
            pass

        # 返回带结果和原因的excel
        # response = HttpResponse(content_type='application/vnd.ms-excel')
        filename = u'用户导入结果反馈'
        # response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
        # report.save(response)
        report.save('media/%s.xls' % filename)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'file': '/media/%s.xls' % filename
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_import Exception:{0}'.format(str(e)))
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


# 导出用户列表
def api_account_export(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        identity = int(request.GET.get("identity", 1))  # 管理员类型，实验人员类型类型
        search = request.GET.get("search", None)  # 搜索关键字
        template = request.GET.get("template", None)  # 是否是模板

        if identity:
            users = Tuser.objects.filter(identity=identity, del_flag=0).filter(Q(name__contains=search) |
                                                                               Q(username__contains=search))

            if template == '1':
                user = users.first()
                users = []
                users.append(user)

            report = xlwt.Workbook(encoding='utf8')
            sheet = report.add_sheet(u'用户列表')
            row = 1
            if identity == 1:  # 实验人员
                title = [u'ID', u'姓名', u'班级', u'所在单位', u'性别', u'指导权限', u'管理权限', u'权限分配责任人']
                for r in users:
                    sheet.write(row, 0, r.username)
                    sheet.write(row, 1, r.name)
                    sheet.write(row, 2, r.tclass.name if r.tclass else '')
                    sheet.write(row, 3, r.tcompany.name if r.tcompany else '')
                    sheet.write(row, 4, '男' if r.gender == 1 else '女')
                    sheet.write(row, 5, '是' if r.director else '否')
                    sheet.write(row, 6, '是' if r.manage else '否')
                    assigned_by = None
                    if r.assigned_by:
                        assigned_by = Tuser.objects.get(id=r.assigned_by)
                    sheet.write(row, 7, assigned_by.name if assigned_by else '')
                    row += 1

            if identity == 2:  # 实验指导
                title = [u'ID', u'姓名', u'姓别', u'QQ', u'昵称', u'所在单位', u'电话', u'邮箱', u'指导权限',
                         u'管理权限', u'权限分配责任人']
                for r in users:
                    sheet.write(row, 0, r.username)
                    sheet.write(row, 1, r.name)
                    sheet.write(row, 2, '男' if r.gender == 1 else '女')
                    sheet.write(row, 3, r.qq)
                    sheet.write(row, 4, r.nickname)
                    sheet.write(row, 5, r.tcompany.name if r.tcompany else '')
                    sheet.write(row, 6, r.phone)
                    sheet.write(row, 7, r.email)
                    sheet.write(row, 8, '是' if r.director else '否')
                    sheet.write(row, 9, '是' if r.manage else '否')
                    assigned_by = None
                    if r.assigned_by:
                        assigned_by = Tuser.objects.get(id=r.assigned_by)
                    sheet.write(row, 10, assigned_by.name if assigned_by else '')
                    row += 1

            if identity == 3 or identity == 4:  # 系统管理员 or # 超级管理员
                title = [u'ID', u'姓名', u'姓别', u'QQ', u'昵称', u'所在单位', u'电话', u'邮箱', u'管理权限',
                         u'权限分配责任人']
                for r in users:
                    sheet.write(row, 0, r.username)
                    sheet.write(row, 1, r.name)
                    sheet.write(row, 2, '男' if r.gender == 1 else '女')
                    sheet.write(row, 3, r.qq)
                    sheet.write(row, 4, r.nickname)
                    sheet.write(row, 5, r.tcompany.name if r.tcompany else '')
                    sheet.write(row, 6, r.phone)
                    sheet.write(row, 7, r.email)
                    sheet.write(row, 8, '是' if r.manage else '否')
                    assigned_by = None
                    if r.assigned_by:
                        assigned_by = Tuser.objects.get(id=r.assigned_by)
                    sheet.write(row, 9, assigned_by.name if assigned_by else '')
                    row += 1

            # 设置样式
            for i in range(0, len(title)):
                sheet.write(0, i, title[i], set_style(220, True))

            response = HttpResponse(content_type='application/vnd.ms-excel')
            filename = urlquote(u'用户列表')
            response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
            report.save(response)
            return response
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_export Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户权限编辑
def api_account_user_auth_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:

        user_id = request.POST.get('id', None)  # 账号
        is_admin = request.POST.get('is_admin', None)  # 超级管理员
        director = request.POST.get('director', None)  # 是否具有指导权限
        manage = request.POST.get('manage', None)  # 是否具有管理权限

        user = Tuser.objects.get(pk=user_id)
        if is_admin:
            user.is_admin = is_admin
        if director:
            user.director = director
        if manage:
            user.manage = manage

        user.save()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_user_auth_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除用户
def api_course_user_delete(request):
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
            item = Tuser.objects.get(pk=delete_id)
            item.del_flag = 1

            # 还有各种关联的东西要判断
            # 我的十二指肠都被绕痛了 这个项目的各种神逻辑回路太长 我现在只想删数据库跑路
            # 一期，二期都是谁设计的业务逻辑， 三期又是谁设计的业务逻辑， 神奇
            # 关联课堂不能被删除的
            cc = CourseClassStudent.objects.filter(student_id=delete_id)
            if cc:
                resp = {'c': 3333, 'm': u'关联课堂不能被删除的'}
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 用户管理-删除实验者指导者功能中，教师如果关联了课堂是不能被删除的
            classes = CourseClass.objects.filter(Q(teacher1_id=delete_id) | Q(teacher2_id=delete_id))
            if classes:
                resp = {'c': 3333, 'm': u'有教师关联了课堂不能被删除的'}
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 关联小组的用户不能被删除
            team_member = TeamMember.objects.filter(user_id=delete_id, del_flag=0)
            if team_member:
                resp = {'c': 3333, 'm': u'关联小组的用户不能被删除'}
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            item.save()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_user_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期 - 共享
def api_account_share(request):
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
        Tuser.objects.filter(id__in=ids).update(is_share=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_account_share Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_get_log_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))
        group_id = request.GET.get("group_id", None)
        company_id = request.GET.get("company_id", None)
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)
        user = request.user
        if request.session['login_type'] == 1:
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        elif request.session['login_type'] == 2:
            group_id = user.allgroups_set.all().first().id
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        elif request.session['login_type'] == 3:
            company_id = user.tcompanymanagers_set.get().tcompany.id
            company = TCompany.objects.get(pk=company_id)
            group_id = company.group.id
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        else:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if search:
            qs = qs.filter(Q(user__username__icontains=search) | Q(user__name__icontains=search) | Q(
                role__name__icontains=search) | Q(login_ip__icontains=search))
        if group_id:
            qs = qs.filter(group__pk=int(group_id))
        if company_id:
            qs = qs.filter(company__pk=int(company_id))
        if start_date:
            qs = qs.filter(login_time__gt=datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            qs = qs.filter(login_time__lte=datetime.strptime(end_date, '%Y-%m-%d'))
        # 分页
        paginator = Paginator(qs, size)
        try:
            logs = paginator.page(page)
        except EmptyPage:
            logs = paginator.page(1)

        results = []
        for log in logs:
            group = log.group is not None and model_to_dict(log.group, fields=['id', 'name']) or None
            company = log.company is not None and model_to_dict(log.company, fields=['id', 'name']) or None
            role = log.role is not None and model_to_dict(log.role, fields=['id', 'name']) or None
            results.append({
                'id': log.id, 'user_id': log.user.username, 'user_name': log.user.name, 'group': group,
                'company': company,
                'role': role, 'login_time': log.login_time is not None and log.login_time.strftime('%Y-%m-%d') or "",
                'login_ip': log.login_ip
            })
        paging = {
            'count': paginator.count,
            'has_previous': logs.has_previous(),
            'has_next': logs.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': logs.number,
        }
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_get_log_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_remove_loginlogs(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        data = request.GET.get("data", None)  # id列表json:[1,2,3]
        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        data = json.loads(data)
        ids_set = set(data)
        ids = [i for i in ids_set]
        LoginLog.objects.filter(id__in=ids).update(del_flag=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_remove_loginlogs Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_export_loginlogs(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] not in [1, 2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.GET.get("search", None)  # 搜索关键字
        group_id = request.GET.get("group_id", None)
        company_id = request.GET.get("company_id", None)
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)

        user = request.user
        if request.session['login_type'] == 1:
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        elif request.session['login_type'] == 2:
            group_id = user.allgroups_set.all().first().id
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        elif request.session['login_type'] == 3:
            company_id = user.tcompanymanagers_set.get().tcompany.id
            company = TCompany.objects.get(pk=company_id)
            group_id = company.group.id
            qs = LoginLog.objects.filter(del_flag=0).order_by("-login_time")
        else:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if search:
            qs = qs.filter(Q(user__username__icontains=search) | Q(user__name__icontains=search) | Q(
                role__name__icontains=search) | Q(login_ip__icontains=search))
        if group_id:
            qs = qs.filter(group__pk=int(group_id))
        if company_id:
            qs = qs.filter(company__pk=int(company_id))
        if start_date:
            qs = qs.filter(login_time__gt=datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            qs = qs.filter(login_time__lte=datetime.strptime(end_date, '%Y-%m-%d'))

        report = xlwt.Workbook(encoding='utf8')
        sheet = report.add_sheet(u'日志列表')
        row = 1
        title = [u'用户名', u'姓名', u'集群', u'单位', u'登录角色', u'登录时间', u'登录IP']
        for log in qs:
            sheet.write(row, 0, log.user.username)
            sheet.write(row, 1, log.user.name)
            sheet.write(row, 2, log.group.name if log.group else '')
            sheet.write(row, 3, log.company.name if log.company else '')
            sheet.write(row, 4, log.role.name if log.role else '')
            sheet.write(row, 5, log.login_time is not None and log.login_time.strftime('%Y-%m-%d') or "")
            sheet.write(row, 6, log.login_ip)
            row += 1
        # 设置样式
        for i in range(0, len(title)):
            sheet.write(0, i, title[i], set_style(220, True))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        filename = urlquote(u'日志列表')
        response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
        report.save(response)
        return response

    except Exception as e:
        logger.exception('api_export_loginlogs Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_get_assistants(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if login_type == 2:
            group = user.allgroups_set.all().first()
            qs = group.groupManagerAssistants.filter(Q(roles=6))
            assistants = []
            for assistant in qs:
                assistant_relation = TGroupManagerAssistants.objects.get(all_groups=group, tuser=assistant)
                actions = list(assistant_relation.actions.all().values())
                assistants.append({
                    'id': assistant.id,
                    'name': assistant.name,
                    'username': assistant.username,
                    'actions': actions
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'assistants': assistants}
        else:
            company = user.tcompanymanagers_set.get().tcompany
            qs = company.assistants.filter(Q(roles=7))
            assistants = []
            for assistant in qs:
                assistant_relation = TCompanyManagerAssistants.objects.get(tcompany=company, tuser=assistant)
                actions = list(assistant_relation.actions.all().values())
                assistants.append({
                    'id': assistant.id,
                    'name': assistant.name,
                    'username': assistant.username,
                    'actions': actions
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'assistants': assistants}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_get_assistants Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_set_assistants(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        login_type = request.session['login_type']
        if login_type not in [2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        candidates = request.POST.get("candidates", None)
        if candidates is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        candidates = json.loads(candidates)
        if login_type == 2:
            group = request.user.allgroups_set.get()
            if not group:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            for candidate in candidates:
                candidateUser = Tuser.objects.get(pk=candidate)
                if not candidateUser:
                    continue
                candidateUser.roles.add(TRole.objects.get(pk=6))
                candidateUser.allgroups_set_assistants.add(group)
        else:
            company = request.user.tcompanymanagers_set.get().tcompany
            if not company:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            for candidate in candidates:
                candidateUser = Tuser.objects.get(pk=candidate)
                if not candidateUser:
                    continue
                candidateUser.roles.add(TRole.objects.get(pk=7))
                candidateUser.t_company_set_assistants.add(company)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_set_assistants Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_unset_assistant(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        login_type = request.session['login_type']
        if login_type not in [2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        candidates = request.POST.get("candidates", None)
        if candidates is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        candidates = json.loads(candidates)
        if login_type == 2:
            group = request.user.allgroups_set.get()
            if not group:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            for candidate in candidates:
                candidateUser = Tuser.objects.get(pk=candidate)
                if not candidateUser:
                    continue
                candidateUser.roles.remove(TRole.objects.get(pk=6))
                candidateUser.allgroups_set_assistants.remove(group)
        else:
            company = request.user.tcompanymanagers_set.get().tcompany
            if not company:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            for candidate in candidates:
                candidateUser = Tuser.objects.get(pk=candidate)
                if not candidateUser:
                    continue
                candidateUser.roles.remove(TRole.objects.get(pk=7))
                candidateUser.t_company_set_assistants.remove(company)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_set_assistants Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_set_assistants_actions(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        login_type = request.session['login_type']
        if login_type not in [2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        assistants_actions = request.POST.get("assistants_actions", None)
        if assistants_actions is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        assistants_actions = json.loads(assistants_actions)
        for assistant_actions in assistants_actions:
            actions = assistant_actions['actions']
            userId = assistant_actions['id']
            if actions is None:
                continue
            assistant = Tuser.objects.get(pk=userId)
            if login_type == 2:
                assistant_relation = TGroupManagerAssistants.objects.get(tuser=assistant)
                for action_id, is_enabled in actions.items():
                    if is_enabled:
                        assistant_relation.actions.add(TAction.objects.get(pk=action_id))
                    else:
                        assistant_relation.actions.remove(TAction.objects.get(pk=action_id))
            else:
                assistant_relation = TCompanyManagerAssistants.objects.get(tuser=assistant)
                for action_id, is_enabled in actions.items():
                    if is_enabled:
                        assistant_relation.actions.add(TAction.objects.get(pk=action_id))
                    else:
                        assistant_relation.actions.remove(TAction.objects.get(pk=action_id))
            resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_set_assistants_actions Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_get_permissions(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        login_type = request.session['login_type']
        qs = TPermission.objects.all()
        permissions = []
        for permission in qs:
            if login_type != 3 and permission.codename == 'code_company_management':
                continue
            if login_type == 3 and permission.codename in ['code_business_management', 'code_group_company_management']:
                continue
            actions = list(permission.taction_set.all().values())
            permission = model_to_dict(permission)
            permission['actions'] = actions
            permissions.append(permission)
        print permissions
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'permissions': permissions}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_get_permissions Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
