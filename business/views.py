#!/usr/bin/python
# -*- coding=utf-8 -*-

# from django.shortcuts import
import json
import logging

from account.models import Tuser
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponse
from experiment.models import *
from business.models import *
from business.service import *
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
from utils.public_fun import getProjectIDByGroupManager
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


def randomString(stringLength=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return ''.join(random.sample(letters, stringLength))


def api_business_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        use_to = request.POST.get("use_to")

        project = Project.objects.get(pk=project_id)

        # 判断项目是否存在
        if project:
            # 验证项目中是否有未配置的跳转项目
            if not check_jump_project(project):
                resp = code.get_msg(code.EXPERIMENT_JUMP_PROJECT_SETUP_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            roles = ProjectRole.objects.filter(project_id=project_id)
            if roles.exists() is False:
                resp = code.get_msg(code.PROJECT_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            with transaction.atomic():
                business = Business.objects.create(project_id=project_id, name=project.name,
                                                   cur_project_id=project_id, created_by=request.user,
                                                   officeItem=project.officeItem)
                business_roles = []
                for item in roles:
                    business_roles.append(BusinessRole(business=business, image_id=item.image_id, name=item.name,
                                                       type=item.type, flow_role_id=item.flow_role_id,
                                                       project_role_id=item.id, project_id=project_id,
                                                       category=item.category, capacity=item.capacity,
                                                       job_type=item.job_type))
                BusinessRole.objects.bulk_create(business_roles)

                # 复制流程角色分配设置
                business_allocations = []
                allocations = ProjectRoleAllocation.objects.filter(project_id=project_id)
                for item in allocations:
                    # 将角色分配中的role_id设置为ProjectRole id
                    role = BusinessRole.objects.filter(business=business, project_role_id=item.role_id).first()
                    if role:
                        business_allocations.append(
                            BusinessRoleAllocation(business=business, node=FlowNode.objects.get(pk=item.node_id),
                                                   project_id=project_id,
                                                   role=role,
                                                   can_start=item.can_start,
                                                   can_terminate=item.can_terminate,
                                                   can_brought=item.can_brought,
                                                   can_take_in=item.can_take_in,
                                                   no=item.no))
                BusinessRoleAllocation.objects.bulk_create(business_allocations)

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': business.id, 'name': u'{0} {1}'.format(business.id, business.name),
                    'project_id': business.project_id,
                    'show_nickname': business.show_nickname, 'start_time': business.start_time,
                    'end_time': business.end_time, 'status': business.status,
                    'created_by': user_simple_info(business.created_by.id) if business.created_by else '',
                    'node_id': business.node.id if business.node else '',
                    'create_time': business.create_time.strftime('%Y-%m-%d')
                }
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)


def api_business_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数
        status = int(request.GET.get("status", 1))  # 实验状态

        user = request.user
        bussinessIDsInTeam = BusinessTeamMember.objects.filter(user=user, del_flag=0).values_list('business_id',
                                                                                                  flat=True)
        qs = Business.objects.filter(
            Q(del_flag=0, pk__in=bussinessIDsInTeam) | Q(created_by=request.user))

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(pk__icontains=search))
            qs = qs.filter(del_flag=0)
        if status == 3:
            qs = qs.filter(Q(status=1) | Q(status=2))
        else:
            qs = qs.filter(status=status)
        paginator = Paginator(qs, size)

        try:
            businesses = paginator.page(page)
        except EmptyPage:
            businesses = paginator.page(1)

        results = []

        for item in businesses:
            team_dict = [model_to_dict(member) for member in BusinessTeamMember.objects.filter(business_id=item.id)]

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

            business = {
                'id': item.id, 'name': u'{0} {1}'.format(item.id, item.name), 'show_nickname': item.show_nickname,
                'start_time': item.start_time.strftime('%Y-%m-%d') if item.start_time else None,
                'end_time': item.end_time.strftime('%Y-%m-%d') if item.end_time else None,
                'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else None,
                'team': team_dict, 'status': item.status, 'created_by': user_simple_info(item.created_by_id),
                'node_id': item.node_id,
                'project': project_dict,
                'huanxin_id': item.huanxin_id,
                'node': cur_node, 'flow_id': project.flow_id if project else None,
                'officeItem': model_to_dict(item.officeItem) if item.officeItem else None
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
        print results
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_business_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        # business_id = request.GET.get("business_id ")  # 实验id
        # business = Business.objects.filter(pk=business_id , del_flag=0).first()
        # if business:
        #     # if not exp.course_class_id:
        #     #     logger.exception('api_experiment_detail Exception:该实验没有注册到课堂')
        #     #     resp = code.get_msg(code.EXPERIMENT_NOT_REGISTER)
        #     #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        #     data = get_experiment_detail(business)
        #
        #     # 三期记录用户最后一次进入的实验id
        #     user = request.user
        #     user.last_business_id = business_id
        #     user.save()
        #
        #     user_role_allocs = []
        #     if business.status == 1:
        #         control_status = 1
        #         path_id = None
        #     else:
        #         path = BusinessTransPath.objects.filter(business=business).last()
        #         control_status = path.control_status
        #         path_id = path.pk
        #         # user_roles = get_roles_status_by_user(exp, path, request.user.pk)
        #         # 三期 - 老师进入实验观察学生做实验  ——ps：二手项目真是个麻烦事
        #         # 获取用户登录类型是老师的
        #         # if request.session['login_type'] == 2:
        #         #     # 老师没有角色就给他创建各种角色， mdzz~zzz， 老师观察者权限
        #         #     p_temp = Project.objects.get(pk=exp.project_id)
        #         #     f_role_temp = FlowRole.objects.filter(flow_id=p_temp.flow_id, name=const.ROLE_TYPE_OBSERVER,
        #         #                                           type=const.ROLE_TYPE_OBSERVER)
        #         #     if not f_role_temp:
        #         #         f_role_temp = FlowRole.objects.create(flow_id=p_temp.flow_id, name=const.ROLE_TYPE_OBSERVER,
        #         #                                               type=const.ROLE_TYPE_OBSERVER, category=99, image_id=40,
        #         #                                               min=1, max=100)
        #         #     else:
        #         #         f_role_temp = f_role_temp.first()
        #         #     p_role_temp = ProjectRole.objects.filter(project_id=exp.project_id, flow_role_id=f_role_temp.id,
        #         #                                              name=const.ROLE_TYPE_OBSERVER,
        #         #                                              type=const.ROLE_TYPE_OBSERVER, )
        #         #     if not p_role_temp:
        #         #         p_role_temp = ProjectRole.objects.create(project_id=exp.project_id, category=99,
        #         #                                                  flow_role_id=f_role_temp.id, image_id=40,
        #         #                                                  name=const.ROLE_TYPE_OBSERVER,
        #         #                                                  type=const.ROLE_TYPE_OBSERVER, )
        #         #     else:
        #         #         p_role_temp = p_role_temp.first()
        #         #     e_role_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=path.node_id,
        #         #                                                       user_id=request.user.id, role_id=p_role_temp.id,
        #         #                                                       path_id=path.pk)
        #         #     if not e_role_temp:
        #         #         e_role_temp = ExperimentRoleStatus.objects.create(experiment_id=experiment_id,
        #         #                                                           node_id=path.node_id, user_id=request.user.id,
        #         #                                                           role_id=p_role_temp.id, path_id=path.pk,
        #         #                                                           sitting_status=const.SITTING_DOWN_STATUS)
        #         #     else:  # 老师默认入席
        #         #         e_role_temp.update(sitting_status=const.SITTING_DOWN_STATUS)
        #         #     # 将老师注册到环信群组
        #         #     easemob_members = []
        #         #     easemob_members.append(request.user.id)
        #         #     easemob_success, easemob_result = easemob.add_groups_member(exp.huanxin_id, easemob_members)
        #         #     pass
        #         # 重新获取一遍user_roles
        #         user_role_allocs_temp = get_role_allocs_status_by_user(business, path, request.user)
        #         # user_roles = []
        #         # 三期 老师以实验指导登录进来，老师只观察只给一个观察者的角色;
        #         # 老师以实验者登录进来，要去掉老师的观察者角色
        #         # if request.session['login_type'] == 2:
        #         #     for role_temp in user_roles_temp:
        #         #         if role_temp['name'] == const.ROLE_TYPE_OBSERVER:
        #         #             user_roles.append(role_temp)
        #         # else:
        #         for role_alloc_temp in user_role_allocs_temp:
        #             if role_alloc_temp['name'] != const.ROLE_TYPE_OBSERVER:
        #                 user_role_allocs.append(role_alloc_temp)
        #
        #         # 取一个角色id
        #         mr = MemberRole.objects.filter(experiment_id=experiment_id, user_id=request.user.pk, del_flag=0).first()
        #         if mr:
        #             data['without_node_user_role_id'] = mr.role_id
        #         # 获取角色相关环节
        #         data['with_user_nodes'] = get_user_with_node(exp, request.user.pk)
        #
        #     data['control_status'] = control_status
        #     data['path_id'] = path_id
        #     data['user_roles'] = user_roles
        #     resp = code.get_msg(code.SUCCESS)
        #     resp['d'] = data
        #
        # else:
        #     resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        #
        # # 三期 - 到达指定环节还有角色没有设置提示设置角色
        # node = business.node
        # if node:
        #     # 已设置的角色
        #     role_list_has = MemberRole.objects.filter(experiment_id=experiment_id, project_id=exp.project_id,
        #                                               del_flag=0)
        #     role_id_list_has = [item.role_id for item in role_list_has]  # 项目角色id
        #     # 环节需要的角色
        #     project_role_need = ProjectRoleAllocation.objects.filter(project_id=exp.project_id, node_id=node.pk)
        #     role_id_list_need = [item.role_id for item in project_role_need]  # 流程角色id
        #     # 没有设置的角色名称
        #     role_name_not_set = []
        #     # 如果当前环节需要的角色还没有设置，则加入到role_name_not_set
        #     for role_id_need_temp in role_id_list_need:
        #         if role_id_need_temp not in role_id_list_has:
        #             role_need_temp = ProjectRole.objects.filter(id=role_id_need_temp).first()
        #             # 除掉老师观察者
        #             if role_need_temp.name != const.ROLE_TYPE_OBSERVER:
        #                 role_name_not_set.append(role_need_temp.name)
        #     if len(role_name_not_set) > 0:
        #         logger.info('当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set))
        #         # resp['c'] = code.get_msg(code.EXPERIMENT_ROLE_NOT_SET)
        #         resp['m'] = '当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set)
        #         data['role_not_set'] = resp['m']
        #         return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_business_start(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.POST.get("business_id")  # get business ID
        business = Business.objects.filter(pk=business_id).first()  # get Business
        logger.info('api_business_start:business_id=%s' % business_id)
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if business.status != 1:
            resp = code.get_msg(code.BUSINESS_HAS_STARTED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # get Project that this business is based on
        project = Project.objects.get(pk=business.project_id)
        # 验证项目中是否有未配置的跳转项目 todo
        if not check_jump_project(project):
            resp = code.get_msg(code.BUSINESS_JUMP_PROJECT_SETUP_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # get First Node ID and Node by project Flow ID
        first_node_id = get_start_node(project.flow_id)
        node = FlowNode.objects.get(pk=first_node_id)
        # get All Business Roles to check if all users are allocated to business Role Alloc
        businessRoles = BusinessRole.objects.filter(business=business)  # get all Business Roles
        for role in businessRoles:
            for no in range(1, role.capacity + 1):
                teamMembers = BusinessTeamMember.objects.filter(business=business, business_role=role, no=no,
                                                                del_flag=0)  # get all team members with same business, role, no to check if user is allocated to this allocation
                if teamMembers.count() == 0:
                    resp = code.get_msg(code.TEAM_MEMBER_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # teamMembers = BusinessTeamMember.objects.filter(business=business, del_flag=0)
        # ids = list(teamMembers.values_list('user_id'))

        # 注册所有的群组用户到环信群组
        # easemob_success, easemob_result = easemob.create_groups(str(business.pk), str(request.user.pk), ids)
        # logger.info(u'easemob create_groups:{}{}'.format(easemob_success, easemob_result))

        # if easemob_success is False:
        #     resp = code.get_msg(code.BUSINESS_START_FAILED)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # get Start Role Allocation
        startRoleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=node, can_start=1, can_take_in=1).first()
        # check if this user is Start User
        isStartUser = BusinessTeamMember.objects.filter(business=business, user=request.user,
                                                        business_role=startRoleAlloc.role,
                                                        no=startRoleAlloc.no).exists()
        if not isStartUser:
            resp = code.get_msg(code.BUSINESS_NO_ACCESS_TO_START)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # get all allocations take part in this first node of this business
        allocations = BusinessRoleAllocation.objects.filter(business=business, node=node, can_take_in=1)
        with transaction.atomic():
            # Create Business TransPath
            path = BusinessTransPath.objects.create(business=business, node=node,
                                                    project_id=business.project_id, task_id=node.task_id, step=1)
            for item in allocations:
                if item.can_brought:
                    come_status = 1
                else:
                    come_status = 9
                # 三期 - 不能直接创建， 在service中结束并走向下一环节的时候会创建角色状态，这里再创建一次就重复了
                brses = BusinessRoleAllocationStatus.objects.filter(business=business, business_role_allocation=item,
                                                                    path=path)
                if brses.count() > 0:  # 存在则更新
                    brs = brses.first()
                    brs.come_status = come_status
                    brs.save()
                else:  # 不存在则创建
                    BusinessRoleAllocationStatus.objects.update_or_create(business=business,
                                                                          business_role_allocation=item,
                                                                          path=path,
                                                                          come_status=come_status)

            # 环信id
            # huanxin_id = easemob_result['data']['groupid']
            # exp.huanxin_id = huanxin_id
            # 设置实验环节为开始环节,改变实验状态
            business.node = node
            business.path_id = path.id
            business.status = 2
            business.save()

        # todo 优化
        user_role_allocs = []
        # teamMembers that I can take part in this business process
        teamMembers = BusinessTeamMember.objects.filter(business=business, user=request.user, del_flag=0)
        for teamMember in teamMembers:
            role_allocs = [model_to_dict(bra) for bra in BusinessRoleAllocation.objects.filter(business=business, node=node, can_take_in=1,
                                                                role=teamMember.business_role,
                                                                no=teamMember.no)]
            user_role_allocs = user_role_allocs + role_allocs

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'node': {
                'id': node.id, 'name': node.name, 'condition': node.condition, 'process_type': node.process.type},
            'huanxin_id': business.huanxin_id, 'user_role_allocs': user_role_allocs, 'id': business_id,
            'flow_id': project.flow_id, 'project_id': project.id
        }
        logger.info('api_business_start end:business_id=%s' % business_id)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_start Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Get No-Deleted Experiments
def api_experiment_list_nodel(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "GET")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            userIDInfo = request.user.id
            projectAvailableList = getProjectIDByGroupManager(userIDInfo)
            search = request.GET.get("search", None)  # 关键字
            page = int(request.GET.get("page", 1))  # 页码
            size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

            qs = Experiment.objects.filter(del_flag=0)
            qs = qs.filter(Q(project_id__in=projectAvailableList) & Q(status=9))

            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(pk__icontains=search))

            paginator = Paginator(qs, size)

            try:
                experiments = paginator.page(page)
            except EmptyPage:
                experiments = paginator.page(1)

            results = []

            for item in experiments:
                course_class = CourseClass.objects.filter(pk=item.course_class_id).first()
                team = Team.objects.filter(pk=item.team_id).first()
                project = Project.objects.filter(pk=item.project_id).first()

                if course_class:
                    course_class_dict = {
                        'id': course_class.id, 'name': course_class.name, 'time': course_class.time,
                        'teacher1': course_class.teacher1.name if course_class.teacher1 else None,
                        'teacher2': course_class.teacher2.name if course_class.teacher2 else None,
                        'term': course_class.term
                    }
                else:
                    course_class_dict = None

                if team:
                    team_dict = {
                        'id': team.id, 'leader': user_simple_info(team.leader), 'open_join': team.open_join,
                        'create_time': team.create_time.strftime('%Y-%m-%d')
                    }
                else:
                    team_dict = None

                if project:
                    project_dict = {
                        'id': project.id, 'name': project.name
                    }
                else:
                    project_dict = None

                can_edit = True if item.created_by == request.user.id or team.leader == request.user.id else False

                node = FlowNode.objects.filter(pk=item.node_id).first()
                if node:
                    cur_node = {
                        'id': node.id, 'name': node.name, 'condition': node.condition,
                        'process_type': node.process.type if node.process else None,
                    }
                else:
                    cur_node = None

                user_roles = []
                exp = {
                    'id': item.id, 'name': item.name, 'show_nickname': item.show_nickname,
                    'start_time': item.start_time.strftime('%Y-%m-%d') if item.start_time else None,
                    'end_time': item.end_time.strftime('%Y-%m-%d') if item.end_time else None,
                    'team': team_dict, 'status': item.status, 'created_by': user_simple_info(item.created_by),
                    'course_class': course_class_dict, 'node_id': item.node_id,
                    'create_time': item.create_time.strftime('%Y-%m-%d'), 'project': project_dict,
                    'huanxin_id': item.huanxin_id, 'can_edit': can_edit,
                    'node': cur_node, 'user_roles': user_roles, 'flow_id': project.flow_id
                }
                results.append(exp)
            # 分页信息
            paging = {
                'count': paginator.count,
                'has_previous': experiments.has_previous(),
                'has_next': experiments.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': experiments.number,
                'page_size': size
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_list Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Get Deleted Experiments
def api_experiment_list_del(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "GET")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            userIDInfo = request.user.id
            projectAvailableList = getProjectIDByGroupManager(userIDInfo)
            search = request.GET.get("search", None)  # 关键字
            page = int(request.GET.get("page", 1))  # 页码
            size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

            qs = Experiment.objects.filter(del_flag=1)
            qs = qs.filter(Q(project_id__in=projectAvailableList) & Q(status=9))

            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(pk__icontains=search))

            paginator = Paginator(qs, size)

            try:
                experiments = paginator.page(page)
            except EmptyPage:
                experiments = paginator.page(1)

            results = []

            for item in experiments:
                course_class = CourseClass.objects.filter(pk=item.course_class_id).first()
                team = Team.objects.filter(pk=item.team_id).first()
                project = Project.objects.filter(pk=item.project_id).first()

                if course_class:
                    course_class_dict = {
                        'id': course_class.id, 'name': course_class.name, 'time': course_class.time,
                        'teacher1': course_class.teacher1.name if course_class.teacher1 else None,
                        'teacher2': course_class.teacher2.name if course_class.teacher2 else None,
                        'term': course_class.term
                    }
                else:
                    course_class_dict = None

                if team:
                    team_dict = {
                        'id': team.id, 'leader': user_simple_info(team.leader), 'open_join': team.open_join,
                        'create_time': team.create_time.strftime('%Y-%m-%d')
                    }
                else:
                    team_dict = None

                if project:
                    project_dict = {
                        'id': project.id, 'name': project.name
                    }
                else:
                    project_dict = None

                can_edit = True if item.created_by == request.user.id or team.leader == request.user.id else False

                node = FlowNode.objects.filter(pk=item.node_id).first()
                if node:
                    cur_node = {
                        'id': node.id, 'name': node.name, 'condition': node.condition,
                        'process_type': node.process.type if node.process else None,
                    }
                else:
                    cur_node = None

                user_roles = []
                exp = {
                    'id': item.id, 'name': item.name, 'show_nickname': item.show_nickname,
                    'start_time': item.start_time.strftime('%Y-%m-%d') if item.start_time else None,
                    'end_time': item.end_time.strftime('%Y-%m-%d') if item.end_time else None,
                    'team': team_dict, 'status': item.status, 'created_by': user_simple_info(item.created_by),
                    'course_class': course_class_dict, 'node_id': item.node_id,
                    'create_time': item.create_time.strftime('%Y-%m-%d'), 'project': project_dict,
                    'huanxin_id': item.huanxin_id, 'can_edit': can_edit,
                    'node': cur_node, 'user_roles': user_roles, 'flow_id': project.flow_id
                }
                results.append(exp)
            # 分页信息
            paging = {
                'count': paginator.count,
                'has_previous': experiments.has_previous(),
                'has_next': experiments.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': experiments.number,
                'page_size': size
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_list Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Delete Business
def api_experiment_delete(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "POST")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            data = request.POST.get("data")  # 实验id数组

            ids = json.loads(data)
            # 排除已经开始的实验
            # Experiment.objects.exclude(status=2).filter(id__in=ids).update(del_flag=1)
            Experiment.objects.filter(id__in=ids).update(del_flag=1)

            resp = code.get_msg(code.SUCCESS)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_delete Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Recovery Business
def api_experiment_recovery(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "POST")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            data = request.POST.get("data")  # 实验id数组

            ids = json.loads(data)
            # 排除已经开始的实验
            # Experiment.objects.exclude(status=2).filter(id__in=ids).update(del_flag=1)
            Experiment.objects.filter(id__in=ids).update(del_flag=0)

            resp = code.get_msg(code.SUCCESS)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_delete Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验结果
def api_experiment_result(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "GET")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            experiment_id = request.GET.get("experiment_id")  # 实验ID
            user_id = request.user.id
            exp = Experiment.objects.filter(pk=experiment_id).first()
            if exp:
                team = Team.objects.filter(pk=exp.team_id).first()
                project = Project.objects.filter(pk=exp.project_id).first()
                flow = Flow.objects.filter(pk=project.flow_id).first()
                members = TeamMember.objects.filter(team_id=exp.team_id, del_flag=0).values_list('user_id', flat=True)
                course_class = CourseClass.objects.filter(pk=exp.course_class_id).first()

                # 小组成员
                member_list = []
                for uid in members:
                    user = Tuser.objects.get(pk=uid)
                    member_list.append(user.name)

                # 组长
                leader = Tuser.objects.filter(pk=team.leader).first()
                # 各环节提交文件信息和聊天信息
                paths = ExperimentTransPath.objects.filter(experiment_id=exp.id)
                node_list = []
                # for item in paths:
                #     # 个人笔记
                #     note = ExperimentNotes.objects.filter(experiment_id=experiment_id,
                #                                           node_id=item.node_id, created_by=user_id).first()
                #
                #     # 角色项目素材
                #     project_doc_list = []
                #     operation_guide_list = []
                #     project_tips_list = []
                #
                #     doc_ids = FlowNodeDocs.objects.filter(flow_id=flow.pk,
                #                                           node_id=item.node_id).values_list('doc_id', flat=True)
                #     if doc_ids:
                #         operation_docs = FlowDocs.objects.filter(id__in=doc_ids, usage__in=(1, 2, 3))
                #         for d in operation_docs:
                #             url = ''
                #             if d.file:
                #                 url = d.file.url
                #             if d.usage == 1:
                #                 operation_guide_list.append({
                #                     'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                #                     'content': d.content, 'url': url, 'file_type': d.file_type
                #                 })
                #             else:
                #                 project_doc_list.append({
                #                     'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                #                     'content': d.content, 'url': url, 'file_type': d.file_type
                #                 })
                #
                #     # 获取该环节角色分配项目素材id
                #     doc_ids = ProjectDocRole.objects.filter(project_id=item.project_id,
                #                                             node_id=item.node_id).values_list('doc_id', flat=True)
                #
                #     if doc_ids:
                #         # logger.info(doc_ids)
                #         project_docs = ProjectDoc.objects.filter(id__in=doc_ids)
                #         for d in project_docs:
                #             if d.usage in [3, 4, 5, 7]:
                #                 is_exist = False
                #                 if d.usage == 3:
                #                     for t in project_doc_list:
                #                         if d.name == t['name']:
                #                             is_exist = True
                #                             break
                #                 if not is_exist:
                #                     project_doc_list.append({
                #                         'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                #                         'content': d.content, 'url': d.file.url, 'file_type': d.file_type
                #                     })
                #
                #     node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first()
                #     print node
                #     doc_list = []
                #     vote_status = []
                #     # ##############################################################################
                #     if node.process.type == 2:
                #         # 如果是编辑
                #         # 应用模板
                #         contents = ExperimentDocContent.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                #                                                        has_edited=True)
                #         for d in contents:
                #             doc_list.append({
                #                 'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                #                 'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                #                 'url': d.file.url if d.file else None
                #             })
                #         # 提交的文件
                #         docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                #                                             path_id=item.pk)
                #         for d in docs:
                #             sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                #             doc_list.append({
                #                 'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                #                 'signs': list(sign_list), 'url': d.file.url if d.file else None
                #             })
                #     elif node.process.type == 3:
                #         project_docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                #                                                     path_id=item.pk)
                #         for d in project_docs:
                #             doc_list.append({
                #                 'id': d.id, 'filename': d.filename, 'signs': [],
                #                 'url': d.file.url if d.file else None, 'content': d.content, 'file_type': d.file_type,
                #             })
                #     elif node.process.type == 5:
                #         vote_status_0_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                                  node_id=item.node_id,
                #                                                                  path_id=item.id, vote_status=0)
                #         vote_status_0 = []
                #         for item0 in vote_status_0_temp:
                #             role_temp = ProjectRole.objects.filter(id=item0.role_id).first()
                #             if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #                 vote_status_0.append(item0)
                #         vote_status_1_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                                  node_id=item.node_id,
                #                                                                  path_id=item.id, vote_status=1)
                #         vote_status_1 = []
                #         for item1 in vote_status_1_temp:
                #             role_temp = ProjectRole.objects.filter(id=item1.role_id).first()
                #             if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #                 vote_status_1.append(item1)
                #         vote_status_2_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                                  node_id=item.node_id,
                #                                                                  path_id=item.id, vote_status=2)
                #         vote_status_2 = []
                #         for item2 in vote_status_2_temp:
                #             role_temp = ProjectRole.objects.filter(id=item2.role_id).first()
                #             if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #                 vote_status_2.append(item2)
                #         vote_status_9_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                                  node_id=item.node_id,
                #                                                                  path_id=item.id, vote_status=9)
                #         vote_status_9 = []
                #         for item9 in vote_status_9_temp:
                #             role_temp = ProjectRole.objects.filter(id=item9.role_id).first()
                #             if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #                 vote_status_9.append(item9)
                #         vote_status = [{'status': '未投票', 'num': len(vote_status_0)},
                #                        {'status': '同意', 'num': len(vote_status_1)},
                #                        {'status': '不同意', 'num': len(vote_status_2)},
                #                        {'status': '弃权', 'num': len(vote_status_9)}]
                #         pass
                #     else:
                #         docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                #                                             path_id=item.id)
                #         for d in docs:
                #             sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                #             doc_list.append({
                #                 'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                #                 'signs': list(sign_list), 'url': d.file.url if d.file else None
                #             })
                #     # 消息
                #     messages = ExperimentMessage.objects.filter(experiment_id=experiment_id,
                #                                                 node_id=item.node_id, path_id=item.id).order_by('timestamp')
                #     message_list = []
                #     for m in messages:
                #         audio = ExperimentMessageFile.objects.filter(pk=m.file_id).first()
                #         message = {
                #             'user_name': m.user_name, 'role_name': m.role_name,
                #             'msg': m.msg, 'msg_type': m.msg_type, 'ext': json.loads(m.ext),
                #             'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                #         }
                #         if audio:
                #             message['url'] = const.WEB_HOST + audio.file.url
                #             message['filename'] = audio.file.name
                #             message['secret'] = ''
                #             message['length'] = audio.length
                #         message_list.append(message)
                #
                #     node_list.append({
                #         'docs': doc_list, 'messages': message_list, 'id': node.id, 'node_name': node.name,
                #         'project_docs': project_doc_list,
                #         'operation_guides': operation_guide_list,
                #         'project_tips_list': project_tips_list,
                #         'note': note.content if note else None, 'type': node.process.type if node.process else 0,
                #         'vote_status': vote_status
                #     })

                detail = {'name': exp.name, 'project_name': project.name,
                          'team_name': team.name, 'members': member_list,
                          'teacher': course_class.teacher1.name if course_class else None,
                          'finish_time': exp.finish_time.strftime('%Y-%m-%d') if exp.finish_time else None,
                          'start_time': exp.start_time.strftime('%Y-%m-%d') if exp.start_time else None,
                          'end_time': exp.end_time.strftime('%Y-%m-%d') if exp.end_time else None,
                          'create_time': exp.create_time.strftime('%Y-%m-%d'),
                          'leader_name': leader.name if leader else None, 'flow_name': flow.name, 'flow_xml': flow.xml,
                          'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
                                                                course_class.term) if course_class else None}
                resp = code.get_msg(code.SUCCESS)
                # resp['d'] = {'detail': detail, 'nodes': node_list}
                resp['d'] = {'detail': detail}
            else:
                resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_result Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
