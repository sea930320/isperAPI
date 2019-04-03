#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging
from django.http import HttpResponse
from django.db import transaction
from team.models import *
from account.models import Tuser
from experiment.models import Experiment, ExperimentRoleStatus
from utils.request_auth import auth_check
from utils import code, const, query

logger = logging.getLogger(__name__)


# 设置组长
def api_team_leader_set(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id")  # 小组
        user_id = request.POST.get("user_id")  # 用户
        user = Tuser.objects.filter(pk=user_id).first()
        if user is None:
            resp = code.get_msg(code.USER_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证小组权限
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader != request.user.pk:
            resp = code.get_msg(code.TEAM_HAS_NOT_PERM)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        team.leader = user_id
        team.save()
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'team_id': team.pk, 'leader': team.leader, 'leader_name': user.name}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_team_leader_set Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 设置小组是否开放
def api_team_open(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id", None)
        open_join = request.POST.get("open", None)
        if team_id is None or open_join is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证小组权限
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader != request.user.pk:
            resp = code.get_msg(code.TEAM_HAS_NOT_PERM)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        team.open_join = int(open_join)
        team.save()
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_open Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 添加小组成员
def api_team_member_add(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id")  # 小组
        data = request.POST.get("data")  # 用户
        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证小组权限
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader != request.user.pk:
            resp = code.get_msg(code.TEAM_HAS_NOT_PERM)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        data = json.loads(data)
        user_ids = TeamMember.objects.filter(team_id=team_id).values_list('user_id', flat=True)
        user_ids_set = set(user_ids)
        ids_set = set(data)
        # 新加成员
        new_ids_set = ids_set - user_ids_set
        new_ids = [i for i in new_ids_set]
        # 原有成员
        old_ids_set = ids_set & user_ids_set
        old_ids = [i for i in old_ids_set]
        with transaction.atomic():
            if len(old_ids) > 0:
                TeamMember.objects.filter(team_id=team_id, user_id__in=old_ids).update(del_flag=0)
            if len(new_ids) > 0:
                new_list = []
                for user_id in new_ids:
                    new_list.append(TeamMember(team_id=team_id, user_id=user_id))
                TeamMember.objects.bulk_create(new_list)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_member_add Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除小组成员
def api_team_member_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id")  # 小组
        user_id = request.POST.get("user_id")  # 用户
        # 验证小组权限
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader != request.user.pk:
            resp = code.get_msg(code.TEAM_HAS_NOT_PERM)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader == int(user_id):
            resp = code.get_msg(code.TEAM_CANNOT_DELETE_SELF)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证是否已参加实验
        # 三期更改， 小组可以重新随意编辑
        # exists = Experiment.objects.filter(team_id=team_id).exists()
        # if exists:
        #     resp = code.get_msg(code.TEAM_HAS_JOIN_EXP)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 三期 小组成员正在另一个实验中不能删除
        # 已经入席不能删除
        # 这什么问题先放一放
        # ers = ExperimentRoleStatus.objects.filter(user_id=user_id, sitting_status=2).exists()
        # if ers:
        #     resp = code.get_msg(code.TEAM_MEMBER_SITING)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        TeamMember.objects.filter(team_id=team_id, user_id=user_id).update(del_flag=1)
        # MemberRole.objects.filter(team_id=team_id, user_id=user_id).delete()
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_member_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除小组
def api_team_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id")  # 小组
        # 验证小组权限
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if team.leader != request.user.pk:
            resp = code.get_msg(code.TEAM_HAS_NOT_PERM)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证是否已参加实验, 如果实验已经全部删除了可以删除小组
        exists = Experiment.objects.filter(team_id=team_id, del_flag=0).exists()
        if exists:
            resp = code.get_msg(code.TEAM_HAS_JOIN_EXP)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        team.del_flag = 1
        team.save()
        TeamMember.objects.filter(team_id=team_id).update(del_flag=1)
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 加入小组
def api_team_member_join(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.POST.get("team_id")  # 小组
        # 验证小组
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        user = request.user
        m = TeamMember.objects.filter(team_id=team_id, user_id=user.pk).first()
        if m:
            m.del_flag = 0
            m.save()
        else:
            TeamMember.objects.create(team_id=team_id, user_id=user.pk)
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_member_join Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 小组成员
def api_team_member(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        team_id = request.GET.get("team_id")  # 小组ID
        if team_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        sql = '''SELECT t.id,t.`name`,t.username,t.type,t.qq,t.gender,c.`name` class_name
        from t_user t LEFT JOIN t_class c ON c.id=t.tclass_id LEFT JOIN t_team_member m ON m.user_id=t.id
        WHERE m.del_flag=0 and t.del_flag=0 and t.is_active=1 and m.team_id=%s''' % team_id
        logger.info(sql)
        team_list = query.select(sql, ['id', 'name', 'username', 'type', 'qq', 'gender', 'class_name'])
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = team_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_member Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 新建小组
def api_team_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        name = request.POST.get("name", None)  # 名称
        open_join = request.POST.get("open_join", None)  # 开放邀请

        # 参数验证
        if name is None or open_join is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exists = Team.objects.filter(name=name, del_flag=0).exists()
        if exists:
            resp = code.get_msg(code.TEAM_HAS_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        user = request.user
        logger.info('leader:%s,name:%s' % (user.pk, name))
        team = Team.objects.create(name=name, leader=user.pk, open_join=open_join, created_by=user.pk)
        TeamMember.objects.create(team_id=team.pk, user_id=user.pk)
        resp = code.get_msg(code.SUCCESS)

        resp['d'] = {'id': team.pk, 'name': team.name, 'open_join': team.open_join, 'leader': team.leader,
                     'leader_name': request.user.name, 'create_time': team.create_time.strftime('%Y-%m-%d')}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 小组列表
def api_team_my(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,
        DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
        from t_team t LEFT JOIN t_user u ON t.leader=u.id LEFT JOIN t_team_member m ON m.team_id=t.id '''
        count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id
        LEFT JOIN t_team_member m ON m.team_id=t.id'''
        where_sql = ' WHERE t.del_flag=0 and (m.user_id=%s or t.leader=%s)' % (request.user.pk, request.user.pk)
        if search:
            where_sql += ' and (t.`name` like \'%' + search + '%\' or u.`name` like \'%' + search + '%\')'

        sql += where_sql
        sql += ' order by t.create_time desc'
        count_sql += where_sql
        logger.info(sql)
        team_list = query.pagination_page(sql, ['id', 'name', 'open_join', 'leader', 'leader_name', 'create_time'],
                                          count_sql, int(page), size)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = team_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_my Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 小组列表
def api_team_other(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        user = request.user
        sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,
        DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
        from t_team t LEFT JOIN t_user u ON t.leader=u.id'''

        count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id'''

        where_sql = ' WHERE t.id not in (SELECT m.team_id from t_team_member m WHERE m.user_id=%s and m.del_flag=0) ' \
                    'and t.del_flag=0 and t.open_join=1 and t.leader!=%s' % (user.pk, user.pk)
        if search:
            where_sql += ' and (t.`name` like \'%' + search + '%\' or u.`name` like \'%' + search + '%\')'

        sql += where_sql
        sql += ' order by t.create_time desc'
        count_sql += where_sql
        logger.info(sql)
        team_list = query.pagination_page(sql, ['id', 'name', 'open_join', 'leader', 'leader_name', 'create_time'],
                                          count_sql, int(page), size)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = team_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_other Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 小组列表
def api_team_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        page = int(request.GET.get("page", 1))  # 页码
        type = int(request.GET.get("type", 1))  # 搜索关键字
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        user = request.user
        if user.type == const.USER_TYPE_STUDENT:
            # 学生
            if type == 1:
                # 指导分配小组，查询老师创建并指定当前学生的小组
                sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,c.`name` class_name,
                DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
                from t_team t LEFT JOIN t_user u ON t.leader=u.id LEFT JOIN t_class c ON c.id=u.tclass_id
                LEFT JOIN t_user e ON t.created_by=e.id'''

                count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id
                LEFT JOIN t_class c ON c.id=u.tclass_id LEFT JOIN t_user e ON t.created_by=e.id'''

                where_sql = ' WHERE t.del_flag=0 and t.leader=%s and e.type=2' % user.pk
            else:
                # 自主建立小组，查询当前学生自主建立小组
                sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,c.`name` class_name,
                DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
                from t_team t LEFT JOIN t_user u ON t.leader=u.id LEFT JOIN t_class c ON c.id=u.tclass_id'''

                count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id
                LEFT JOIN t_class c ON c.id=u.tclass_id'''

                where_sql = ' WHERE t.del_flag=0 and t.created_by=%s' % user.pk
        else:
            # 老师
            if type == 1:
                # 指导分配小组，查询老师创建并指定当前学生的小组
                # 自主建立小组，查询所有学生自主建立小组
                sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,c.`name` class_name,
                    DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
                    from t_team t LEFT JOIN t_user u ON t.leader=u.id LEFT JOIN t_class c ON c.id=u.tclass_id
                    LEFT JOIN t_user e ON t.created_by=e.id'''

                count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id
                    LEFT JOIN t_class c ON c.id=u.tclass_id LEFT JOIN t_user e ON t.created_by=e.id'''

                where_sql = ' WHERE t.del_flag=0 and t.created_by=%s' % user.pk
            else:
                # 自主建立小组，查询所有学生自主建立小组
                sql = '''SELECT DISTINCT(t.id),t.`name`,t.open_join,t.leader,u.`name` leader_name,c.`name` class_name,
                    DATE_FORMAT(t.create_time,'%Y-%m-%d') create_time
                    from t_team t LEFT JOIN t_user u ON t.leader=u.id LEFT JOIN t_class c ON c.id=u.tclass_id
                    LEFT JOIN t_user e ON t.created_by=e.id'''

                count_sql = '''SELECT count(DISTINCT(t.id)) from t_team t LEFT JOIN t_user u ON t.leader=u.id
                    LEFT JOIN t_class c ON c.id=u.tclass_id LEFT JOIN t_user e ON t.created_by=e.id'''

                where_sql = ' WHERE t.del_flag=0 and e.type=1'
        sql += where_sql
        sql += ' order by t.create_time desc'
        count_sql += where_sql
        logger.info(sql)
        team_list = query.pagination_page(sql, ['id', 'name', 'open_join', 'leader', 'leader_name', 'class_name',
                                                'create_time'],
                                          count_sql, int(page), size)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = team_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 创建小组和小组成员,设置组长
def api_team_create_v3(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        name = request.POST.get("name", None)  # 小组名称
        open_join = request.POST.get("open_join", None)  # 开放邀请
        data = request.POST.get("data")  # 小组用户
        user_id = request.POST.get("user_id")  # 组长用户id

        # 参数验证
        if name is None or open_join is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        user = Tuser.objects.filter(pk=user_id).first()
        if user is None:
            resp = code.get_msg(code.USER_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # ------------------------------ 创建小组逻辑 begin
        exists = Team.objects.filter(name=name, del_flag=0).exists()
        if exists:
            resp = code.get_msg(code.TEAM_HAS_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        user = request.user
        logger.info('leader:%s,name:%s' % (user.pk, name))
        team = Team.objects.create(name=name, leader=user_id, open_join=open_join, created_by=user.pk)
        TeamMember.objects.create(team_id=team.pk, user_id=user.pk)
        # ------------------------------ 创建小组逻辑 end

        team_id = team.pk

        # ------------------------------ 增加小组成员 begin

        data = json.loads(data)
        user_ids = TeamMember.objects.filter(team_id=team_id).values_list('user_id', flat=True)
        user_ids_set = set(user_ids)
        ids_set = set(data)
        # 新加成员
        new_ids_set = ids_set - user_ids_set
        new_ids = [i for i in new_ids_set]
        # 原有成员
        old_ids_set = ids_set & user_ids_set
        old_ids = [i for i in old_ids_set]
        with transaction.atomic():
            if len(old_ids) > 0:
                TeamMember.objects.filter(team_id=team_id, user_id__in=old_ids).update(del_flag=0)
            if len(new_ids) > 0:
                new_list = []
                for user_id in new_ids:
                    new_list.append(TeamMember(team_id=team_id, user_id=user_id))
                TeamMember.objects.bulk_create(new_list)
        # ------------------------------ 增加小组成员 end

        # ------------------------------ 设置组长begin
        # team.leader = user_id
        # team.save()
        # ------------------------------ 设置组长end

        resp = code.get_msg(code.SUCCESS)

        resp['d'] = {'id': team.pk, 'name': team.name, 'open_join': team.open_join, 'leader': team.leader,
                     'leader_name': request.user.name, 'create_time': team.create_time.strftime('%Y-%m-%d')}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_team_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    pass


