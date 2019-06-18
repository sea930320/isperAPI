#!/usr/bin/python
# -*- coding=utf-8 -*-

# from django.shortcuts import
import json
import logging
import random

from account.models import Tuser, TNotifications, TInnerPermission
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count
from django.http import HttpResponse
from experiment.models import *
from business.models import *
from business.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation, \
    FlowRoleAllocationAction, ProcessRoleAllocationAction
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
                if project.created_role_id in [3, 7]:
                    company_id = project.created_by.tcompanymanagers_set.get().tcompany.id if project.created_role_id == 3 else project.created_by.t_company_set_assistants.get().id if project.created_role_id == 7 else None
                business = Business.objects.create(
                    project_id=project_id,
                    name=project.name,
                    cur_project_id=project_id,
                    created_by=request.user,
                    officeItem=project.officeItem,
                    target_company_id=use_to if project.created_role_id in [2,
                                                                            6] else company_id if project.created_role_id in [
                        3, 7] and project.use_to_id is None else None,
                    target_part_id=project.use_to_id if project.created_role_id in [3,
                                                                                    7] and project.use_to_id is not None else None,
                )
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
                    project = Project.objects.filter(pk=item.project_id).first()
                    projectRole = ProjectRole.objects.filter(pk=item.role_id).first()
                    if project is None or projectRole is None:
                        continue
                    flow_role_alloc = FlowRoleAllocation.objects.filter(flow_id=project.flow_id, node_id=item.node_id,
                                                                        role_id=projectRole.flow_role_id,
                                                                        no=item.no).first()
                    if flow_role_alloc is None:
                        continue
                    if role:
                        business_allocations.append(
                            BusinessRoleAllocation(business=business, node=FlowNode.objects.get(pk=item.node_id),
                                                   project_id=project_id,
                                                   project_role_alloc_id=item.id,
                                                   flow_role_alloc_id=flow_role_alloc.id,
                                                   role=role,
                                                   can_start=item.can_start,
                                                   can_terminate=item.can_terminate,
                                                   can_brought=item.can_brought,
                                                   can_take_in=item.can_take_in,
                                                   no=item.no))
                BusinessRoleAllocation.objects.bulk_create(business_allocations)

                teammates_configuration(business.id, [])

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
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def teammates_configuration(business_id, seted_users_fromInnerPermission):

    # check team counts

    business_team_counts = list(BusinessRole.objects.filter(business_id=business_id).values('job_type__name', 'capacity'))
    business = Business.objects.get(id=business_id)

    project = Project.objects.get(pk=business.project_id)
    first_node_id = get_start_node(project.flow_id)
    node = FlowNode.objects.get(pk=first_node_id)
    startRoleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=node, can_start=1,
                                                           can_take_in=1).first()
    for item in business_team_counts:
        if item['job_type__name'] == startRoleAlloc.role.name:
            item['capacity'] -= 1

    company_id = None
    target_user_counts = []
    if business.target_part is not None:
        target_user_counts = list(Tuser.objects.filter(Q(tposition__parts_id=business.target_part.id, is_review=1) & ~Q(id=business.created_by_id)).values('tposition__name').annotate(counts=Count('id')))
        company_id = business.target_part.company_id
    elif business.target_company is not None:
        target_user_counts = list(Tuser.objects.filter(Q(tcompany=business.target_company, is_review=1) & ~Q(id=business.created_by_id)).values('tposition__name').annotate(counts=Count('id')))
        company_id = business.target_company.id

    if seted_users_fromInnerPermission:
        for xs in seted_users_fromInnerPermission:
            xIndex = next((index for (index, xt) in enumerate(target_user_counts) if xt['tposition__name'] == xs['role_name']), None)
            if xIndex is None:
                target_user_counts.append({'tposition__name': xs['role_name'], 'counts': 1})
            else:
                target_user_counts[xIndex]['counts'] += 1

    moreResult = []
    for item in business_team_counts:
        matched_item = next((x for x in target_user_counts if x['tposition__name'] == item['job_type__name']), None)
        if matched_item is None:
            moreResult.append({'role_name': item['job_type__name'], 'moreCount': item['capacity']})
        elif matched_item['counts'] < item['capacity']:
            moreResult.append({'role_name': item['job_type__name'], 'moreCount': item['capacity'] - matched_item['counts']})

    if moreResult:
        if len(seted_users_fromInnerPermission) != 0:
            return
        if TInnerPermission.objects.get(id=1).ownPositions.filter(parts__company_id=company_id).count() != 0\
                and TInnerPermission.objects.get(id=1).ownPositions.filter(parts__company_id=company_id).filter(tuser__isnull=False).values_list('tuser', flat=True).count() != 0:
            newNotification = TNotifications.objects.create(
                type='businessMoreTeammate_' + str(business_id),
                content=str(moreResult),
                link='business-moreTeammates',
                role_id=5,
                mode=0
            )
            newNotification.save()
            for userID in TInnerPermission.objects.get(id=1).ownPositions.filter(parts__company_id=company_id).filter(tuser__isnull=False).values_list('tuser', flat=True):
                newNotification.targets.add(Tuser.objects.get(id=userID))
        elif TInnerPermission.objects.get(id=1).ownPositions.filter(parts__company_id=company_id).count() == 0\
                or TInnerPermission.objects.get(id=1).ownPositions.filter(parts__company_id=company_id).filter(tuser__isnull=False).values_list('tuser', flat=True).count() == 0:
            newNotification = TNotifications.objects.create(
                type='businessMoreTeammate_' + str(business_id),
                content=str(moreResult),
                link='manager-moreTeammates',
                role_id=3,
                mode=0
            )
            newNotification.save()
            for userItem in TCompany.objects.get(id=company_id).tcompanymanagers_set.all():
                newNotification.targets.add(userItem.tuser)
        return

    # configuration team

    targetUnitUsers = []
    teammateList = list(BusinessRoleAllocation.objects.filter(business_id=business_id).values('role_id', 'role__job_type__name', 'no').distinct())
    if business.target_part is not None:
        targetUnitUsers = [{
                'id': item.id,
                'position': item.tposition.name,
            } for item in Tuser.objects.filter(Q(tposition__parts_id=business.target_part.id, is_review=1) & ~Q(id=business.created_by_id))]
    elif business.target_company is not None:
        targetUnitUsers = [{
                'id': item.id,
                'position': item.tposition.name if item.tposition else None,
            } for item in Tuser.objects.filter(Q(tcompany_id=company_id, is_review=1) & ~Q(id=business.created_by_id))]

    newTeammate = BusinessTeamMember.objects.create(
        business_id=business_id,
        user_id=business.created_by_id,
        business_role_id=startRoleAlloc.role_id,
        no=startRoleAlloc.no,
        del_flag=0,
        project_id=business.project_id
    )
    newTeammate.save()

    if seted_users_fromInnerPermission:
        for item in seted_users_fromInnerPermission:
            targetUnitUsers.append({'position': item['role_name'], 'id': item['userId']})

    for teamItem in teammateList:
        selectedUser = random.choice([a for a in targetUnitUsers if a['position'] == teamItem['role__job_type__name']])
        targetUnitUsers.pop(next((index for (index, x) in enumerate(targetUnitUsers) if x == selectedUser), None))
        newTeammate = BusinessTeamMember.objects.create(
            business_id=business_id,
            user_id=selectedUser['id'],
            business_role_id=teamItem['role_id'],
            no=teamItem['no'],
            del_flag=0,
            project_id=business.project_id
        )
        newTeammate.save()

        Business.objects.filter(id=business_id).update(status=2)

    return 'team_configured'


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
        business_id = request.GET.get("business_id")  # 实验id

        if BusinessTransPath.objects.filter(business_id=business_id).count() == 0:
            resp = api_business_start(request)
            if resp != 'success':
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business:
            data = get_business_detail(business)

            # 三期记录用户最后一次进入的实验id
            user = request.user
            user.last_business_id = business_id
            user.save()

            user_role_allocs = []
            if business.status == 1:
                control_status = 1
                path_id = None
            else:
                path = BusinessTransPath.objects.filter(business=business).last()
                control_status = path.control_status
                path_id = path.pk
                user_role_allocs_temp = get_role_allocs_status_by_user(business, path, request.user)
                for role_alloc_temp in user_role_allocs_temp:
                    if role_alloc_temp['role']['type'] != const.ROLE_TYPE_OBSERVER:
                        user_role_allocs.append(role_alloc_temp)

                data['with_user_nodes'] = get_user_with_node_on_business(business, request.user)

            data['control_status'] = control_status
            data['path_id'] = path_id
            data['user_role_allocs'] = user_role_allocs
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 三期 - 到达指定环节还有角色没有设置提示设置角色
        node = business.node
        if node:
            role_name_not_set = []
            role_allocs_node = BusinessRoleAllocation.objects.filter(business=business, node=node,
                                                                     project_id=business.cur_project_id,
                                                                     can_take_in=True)
            for role_alloc in role_allocs_node:
                btmExist = BusinessTeamMember.objects.filter(business=business, business_role=role_alloc.role,
                                                             no=role_alloc.no, project_id=business.cur_project_id,
                                                             del_flag=0).exists()
                if btmExist and role_alloc.role.type != const.ROLE_TYPE_OBSERVER:
                    continue
                role_name_not_set.append(role_alloc.role.name)
            if len(role_name_not_set) > 0:
                logger.info('当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set))
                # resp['c'] = code.get_msg(code.EXPERIMENT_ROLE_NOT_SET)
                resp['m'] = '当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set)
                data['role_not_set'] = resp['m']
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_business_start(request):
    business_id = request.GET.get("business_id")  # 实验id
    business = Business.objects.filter(pk=business_id).first()  # get Business
    logger.info('api_business_start:business_id=%s' % business_id)
    if business is None:
        resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return resp

    # get Project that this business is based on
    project = Project.objects.get(pk=business.project_id)
    # 验证项目中是否有未配置的跳转项目 todo
    if not check_jump_project(project):
        resp = code.get_msg(code.BUSINESS_JUMP_PROJECT_SETUP_ERROR)
        return resp
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
                return resp

    # teamMembers = BusinessTeamMember.objects.filter(business=business, del_flag=0)
    # ids = list(teamMembers.values_list('user_id'))

    # 注册所有的群组用户到环信群组
    # easemob_success, easemob_result = easemob.create_groups(str(business.pk), str(request.user.pk), ids)
    # logger.info(u'easemob create_groups:{}{}'.format(easemob_success, easemob_result))

    # if easemob_success is False:
    #     resp = code.get_msg(code.BUSINESS_START_FAILED)
    #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    # get Start Role Allocation
    startRoleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=node, can_start=1,
                                                           can_take_in=1).first()
    # check if this user is Start User
    isStartUser = BusinessTeamMember.objects.filter(business=business, user=request.user,
                                                    business_role=startRoleAlloc.role,
                                                    no=startRoleAlloc.no).exists()
    if not isStartUser:
        resp = code.get_msg(code.BUSINESS_NO_ACCESS_TO_START)
        return resp
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
        business.save()

    return 'success'


# 实验环节详情
def api_business_node_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        roleAllocID = request.GET.get("roleAllocID", None)  # 角色id

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=business.cur_project_id)

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.BUSINESS_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 获取上个环节
        pre_node = get_business_pre_node_path(business)
        pre_node_id = None
        if pre_node:
            pre_node_id = pre_node.node_id

        path = BusinessTransPath.objects.filter(business=business).last()

        # 当前用户可选角色
        role_alloc_list_temp = get_role_allocs_status_by_user(business, path, request.user)

        role_alloc_list = []

        # 三期 老师以实验指导登录进来，老师只观察只给一个观察者的角色;老师以实验者登录进来，要去掉老师的观察者角色
        if request.session['login_type'] == 2:
            for role_alloc_temp in role_alloc_list_temp:
                if role_alloc_temp['role']['name'] == const.ROLE_TYPE_OBSERVER:
                    role_alloc_list.append(role_alloc_temp)
        else:
            for role_alloc_temp in role_alloc_list_temp:
                if role_alloc_temp['role']['name'] != const.ROLE_TYPE_OBSERVER:
                    role_alloc_list.append(role_alloc_temp)

        # 当前环节所有角色状态
        role_alloc_status_list_temp = get_all_simple_role_allocs_status(business, node, path)

        role_alloc_status_list = []
        # 三期 老师以实验指导登录进来, 不显示老师角色
        # 这
        for role_alloc_temp in role_alloc_status_list_temp:
            if role_alloc_temp['role_name'] != const.ROLE_TYPE_OBSERVER:
                role_alloc_status_list.append(role_alloc_temp)

        # 是否投票
        has_vote = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                               business_role_allocation_id=roleAllocID,
                                                               business_role_allocation__can_take_in=1,
                                                               business_role_allocation__node=node,
                                                               path=path, vote_status=0).exists()
        if path.vote_status == 1:
            end_vote = False
        else:
            end_vote = True

        # 场景动作列表
        process_action_list = []
        # 场景信息
        if node.process:
            pro = node.process
            process = {
                'id': pro.id, 'name': pro.name, 'type': pro.type, 'can_switch': pro.can_switch,
                'file': pro.file.url if pro.file else None,
                'image': pro.image.url if pro.image else None
            }
        else:
            process = None

        # 查询小组组长
        can_opt = True if business.created_by == request.user else False

        # 实验心得
        # experience = ExperimentExperience.objects.filter(experiment_id=exp.id, created_by=request.user.pk).first()
        # experience_data = {'status': 1, 'content': ''}
        # if experience:
        #     experience_data = {
        #         'id': experience.id, 'content': experience.content, 'status': experience.status,
        #         'created_by': user_simple_info(experience.created_by),
        #         'create_time': experience.create_time.strftime('%Y-%m-%d')
        #     }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'role_allocs': role_alloc_list, 'process': process, 'process_actions': process_action_list,
            'can_opt': can_opt,
            'role_alloc_status': role_alloc_status_list, 'id': business.id, 'name': business.name,
            # 'experience': experience_data,
            'node': {'id': node.id, 'name': node.name, 'condition': node.condition}, 'pre_node_id': pre_node_id,
            'huanxin_id': business.huanxin_id, 'control_status': path.control_status,
            'entire_graph': project.entire_graph,
            # 'leader': team.leader if team else None,
            'flow_id': project.flow_id, 'has_vote': False if has_vote else True, 'end_vote': end_vote
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_business_trans_path(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.GET.get("business_id")  # 实验ID
        # 判断实验是否存在
        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business:
            if business.status == const.EXPERIMENT_FINISHED:
                node = {'is_finished': True}
            else:
                next_node = FlowNode.objects.filter(pk=business.node_id).first()
                node = {'node_id': next_node.pk, 'task_id': next_node.task_id,
                        'name': next_node.name, 'is_finished': False}

            project = Project.objects.get(pk=business.cur_project_id)
            paths = BusinessTransPath.objects.filter(business_id=business.id,
                                                     project_id=business.cur_project_id).values_list('task_id',
                                                                                                     flat=True)
            flow = Flow.objects.get(pk=project.flow_id)
            xml = bpmn_color(flow.xml, list(paths))

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'business_id': business.pk, 'business_name': business.name, 'flow_id': flow.pk,
                         'flow_name': flow.name,
                         'xml': xml, 'node': node}
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
    except Exception as e:
        logger.exception('api_business_trans_path Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节聊天消息列表
def api_business_node_messages(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id")  # 实验ID
        node_id = request.GET.get("node_id", None)  # 环节id
        is_paging = int(request.GET.get('is_paging', 1))  # 是否进行分页（1，分页；0，不分页）
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        business = Business.objects.filter(pk=business_id).first()
        if business:
            path = BusinessTransPath.objects.filter(business_id=business_id).last()
            data = get_node_path_messages_on_business(business, node_id, path.pk, is_paging, page, size)

            for i in range(len(data['results'])):
                file_id = data['results'][i]['file_id']
                mid = data['results'][i]['id']
                m_ext = data['results'][i]['ext']
                opt_status = data['results'][i]['opt_status']

                # 更新扩展
                ext = json.loads(m_ext)
                ext['id'] = mid
                ext['business_role_alloc'] = model_to_dict(BusinessRoleAllocation.objects.filter(pk=ext['role_alloc_id']).first())
                if opt_status == 1:
                    ext['opt_status'] = True
                else:
                    ext['opt_status'] = False

                data['results'][i]['type'] = 'groupchat'
                data['results'][i]['ext'] = ext
                data['results'][i]['to'] = business.huanxin_id

                # 音频文件
                if file_id:
                    audio = BusinessMessageFile.objects.filter(pk=file_id).first()
                    if audio:
                        # data['results'][i]['url'] = const.WEB_HOST + audio.file.url
                        data['results'][i]['url'] = const.WEB_HOST + audio.file.url
                        data['results'][i]['filename'] = audio.file.name
                        data['results'][i]['secret'] = ''
                        data['results'][i]['length'] = audio.length

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_node_messages Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验功能按钮
def api_business_node_function(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_alloc_id = request.GET.get("role_alloc_id", None)  # 角色id

        user_id = request.user.id
        business = Business.objects.filter(pk=business_id).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.filter(pk=business.cur_project_id).first()
        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.BUSINESS_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = BusinessTransPath.objects.filter(business_id=business_id).last()
        # 判断该实验环节是否存在该角色
        if role_alloc_id is None:
            brases = BusinessRoleAllocationStatus.objects.filter(business_id=business_id,
                                                                 business_role_allocation__node_id=node_id,
                                                                 business_role_allocation__project_id=business.cur_project_id,
                                                                 path_id=path.pk)
            role_alloc = None
            for bras in brases:
                bra = bras.business_role_allocation
                btm = BusinessTeamMember.objects.filter(business=business, user_id=user_id, business_role=bra.role,
                                                        no=bra.no, del_flag=0, project_id=business.cur_project_id)
                if btm.exists():
                    role_alloc = bra
                    break;
            if role_alloc is None:
                resp = code.get_msg(code.BUSINESS_NODE_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            else:
                role_alloc_id = role_alloc.id

        role_alloc_status = BusinessRoleAllocationStatus.objects.filter(business_id=business_id,
                                                                        business_role_allocation_id=role_alloc_id).first()
        if role_alloc_status is None:
            resp = code.get_msg(code.BUSINESS_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 三期 - 根据上一步骤自动入席 判断是否入席
        bps = BusinessPositionStatus.objects.filter(business_id=business_id,
                                                    business_role_allocation__node_id=path.node_id, path_id=path.id,
                                                    business_role_allocation_id=role_alloc_id)
        if bps:
            business_position_status = bps.first()
            if business_position_status.sitting_status == 2:  # 已入席
                role_alloc_status.sitting_status = const.SITTING_DOWN_STATUS

        # 用户角色状态
        # 当前用户可选角色
        role_alloc_list = get_role_allocs_status_simple_by_user(business, node, path, user_id)

        # 功能动作列表根据环节和角色分配过滤
        role_alloc = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
        flow_action_ids = []
        process_action_ids = []
        if role_alloc:
            flow_actions = FlowRoleAllocationAction.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                   role_allocation_id=role_alloc.flow_role_alloc_id,
                                                                   del_flag=0).first()

            process_actions = ProcessRoleAllocationAction.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                         role_allocation_id=role_alloc.flow_role_alloc_id,
                                                                         del_flag=0).first()
            if process_actions and process_actions.actions:
                process_action_ids = json.loads(process_actions.actions)
            else:
                process_action_ids = [58, 60, 61]
            if flow_actions and flow_actions.actions:
                flow_action_ids = json.loads(flow_actions.actions)
            else:
                flow_action_ids = [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34]

        # 当前角色动画
        process_action_list = get_role_alloc_process_actions(business, path, role_alloc_id, process_action_ids)

        # 功能按钮
        # 是否有结束环节的权限
        can_terminate = role_alloc.can_terminate

        function_action_list = []
        function_actions = FlowAction.objects.filter(id__in=flow_action_ids, del_flag=0)

        # 判断按钮是否可用
        for item in function_actions:
            if can_terminate:
                disable = False
            else:
                disable = False
                # 判断表达管理
                if path.control_status == 2:
                    if role_alloc_status:
                        if item.cmd == const.ACTION_DOC_SHOW:
                            if role_alloc_status.show_status != 1:
                                disable = True
                        if item.cmd == const.ACTION_DOC_SUBMIT:
                            if role_alloc_status.submit_status != 1:
                                disable = True
                    else:
                        disable = True
                else:
                    # 申请发言状态
                    if item.cmd == const.ACTION_ROLE_APPLY_SPEAK:
                        disable = True
                    if item.cmd == const.ACTION_DOC_APPLY_SUBMIT:
                        disable = True
                    if item.cmd == const.ACTION_DOC_APPLY_SHOW:
                        disable = True

            # 入席、退席互斥
            if role_alloc_status.sitting_status == const.SITTING_UP_STATUS:
                if item.cmd == const.ACTION_ROLE_LETOUT or item.cmd == const.ACTION_ROLE_LETIN \
                        or item.cmd == const.ACTION_ROLE_REQUEST_SIGN or item.cmd == const.ACTION_ROLE_SCHEDULE_REPORT \
                        or item.cmd == const.ACTION_ROLE_HIDE:
                    disable = True
                    # 约见
                    # if item.cmd == const.ACTION_ROLE_MEET and not can_brought:
                    #     disable = True
            else:
                if item.cmd == const.ACTION_ROLE_SHOW:
                    disable = True

                if item.cmd == const.ACTION_ROLE_HIDE:
                    report_exists = BusinessReportStatus.objects.filter(business_id=business_id,
                                                                        business_role_allocation__node_id=node_id,
                                                                        path_id=path.id,
                                                                        business_role_allocation_id=role_alloc_id,
                                                                        schedule_status=const.SCHEDULE_UP_STATUS).exists()
                    if report_exists:
                        disable = True

                # 起立坐下互斥
                if item.cmd == const.ACTION_ROLE_STAND:
                    if role_alloc_status.stand_status == 1:
                        disable = True

                if item.cmd == const.ACTION_ROLE_SITDOWN:
                    if role_alloc_status.stand_status == 2:
                        disable = True
                # 约见
                if item.cmd == const.ACTION_ROLE_MEET:
                    disable = True

            # 判断报告按钮状态
            if item.cmd == const.ACTION_ROLE_TOWARD_REPORT:
                disable = True
                report_exists = BusinessReportStatus.objects.filter(business_id=business_id,
                                                                    business_role_allocation__node_id=node_id,
                                                                    path_id=path.id,
                                                                    business_role_allocation_id=role_alloc_id,
                                                                    schedule_status=const.SCHEDULE_OK_STATUS).exists()
                if report_exists:
                    disable = False

            if item.cmd == const.ACTION_ROLE_EDN_REPORT:
                disable = True
                report_exists = BusinessReportStatus.objects.filter(business_id=business_id,
                                                                    business_role_allocation__node_id=node_id,
                                                                    path_id=path.id,
                                                                    business_role_allocation_id=role_alloc_id,
                                                                    schedule_status=const.SCHEDULE_UP_STATUS).exists()
                if report_exists:
                    disable = False

            btn = {
                'id': item.id, 'name': item.name, 'cmd': item.cmd, 'disable': disable
            }
            function_action_list.append(btn)

        resp = code.get_msg(code.SUCCESS)

        # 三期，如果进来的是老师观察者角色， 没有任何功能按钮， tmd
        if role_alloc.role.type == const.ROLE_TYPE_OBSERVER:
            function_action_list = []
            process_action_list = []

        resp['d'] = {'function_action_list': function_action_list,
                     'process_action_list': process_action_list,
                     'user_role_allocs': role_alloc_list}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_node_function Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_business_node_role_docs(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_alloc_id = request.GET.get("role_alloc_id", None)  # 角色id

        user = request.user
        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        if business is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=business.cur_project_id)

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.BUSINESS_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = BusinessTransPath.objects.filter(business_id=business_id).last()
        # 判断该实验环节是否存在该角色
        if role_alloc_id is None:
            brases = BusinessRoleAllocationStatus.objects.filter(business_id=business_id,
                                                                 business_role_allocation__node_id=node_id,
                                                                 business_role_allocation__project_id=business.cur_project_id,
                                                                 path_id=path.pk)
            role_alloc = None
            for bras in brases:
                bra = bras.business_role_allocation
                btm = BusinessTeamMember.objects.filter(business=business, user_id=user.id, business_role=bra.role,
                                                        no=bra.no, del_flag=0, project_id=business.cur_project_id)
                if btm.exists():
                    role_alloc = bra
                    break;
            if role_alloc is None:
                resp = code.get_msg(code.BUSINESS_NODE_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            else:
                role_alloc_id = role_alloc.id

        # 获取该环节角色项目所有素材
        docs = get_node_role_alloc_docs(business, node_id, project.pk, project.flow_id, role_alloc_id)

        # 前面所有环节素材
        pre_doc_list = get_pre_node_role_alloc_docs(business, node_id, project.pk, role_alloc_id)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'operation_guides': docs['operation_guides'],
            'project_tips_list': docs['project_tips_list'],
            'cur_doc_list': docs['cur_doc_list'],
            'pre_doc_list': pre_doc_list,
            'id': business.id, 'name': business.name,
            'flow_id': project.flow_id
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_node_role_docs Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_business_messages(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id")  # 实验ID
        business = Business.objects.filter(pk=business_id).first()
        if business:
            paths = BusinessTransPath.objects.filter(business_id=business_id)
            node_list = []
            for item in paths:
                messages = BusinessMessage.objects.filter(business_id=business_id,
                                                          business_role_allocation__node_id=item.node_id,
                                                          path_id=item.id).order_by(
                    'timestamp')
                message_list = []
                for m in messages:
                    ext = json.loads(m.ext)
                    ext['id'] = m.id
                    ext['opt_status'] = m.opt_status
                    message = {
                        'id': m.id, 'from': m.user_id, 'to': business.huanxin_id, 'msg_type': m.msg_type,
                        'data': m.msg, 'type': 'groupchat', 'ext': ext
                    }
                    if m.file_id:
                        audio = BusinessMessageFile.objects.filter(pk=m.file_id).first()
                        if audio:
                            message['url'] = const.WEB_HOST + audio.file.url
                            message['filename'] = audio.file.name
                            message['secret'] = ''
                            message['length'] = audio.length

                    message_list.append(message)
                node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first()
                node_list.append({
                    'id': node.id, 'name': node.name, 'process_type': node.process.type,
                    'messages': message_list, 'count': messages.count()
                })

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': node_list}
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_messages Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

# 实验文件展示列表
def api_business_file_display_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        path_id = request.GET.get("path_id", None)  # 环节id

        business = Business.objects.filter(pk=business_id).first()
        if business:
            doc_list = get_business_display_files(business, node_id, path_id)
            # 分页信息
            paging = {
                'count': len(doc_list),
                'has_previous': False,
                'has_next': False,
                'num_pages': 1,
                'cur_page': 1,
            }
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': doc_list, 'paging': paging}

        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_file_display_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

# 实验所属项目素材查询
def api_business_templates(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        role_alloc_id = request.GET.get('role_alloc_id', None)
        usage = request.GET.get("usage", None)  # 用途

        if None in (business_id, node_id):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        business = Business.objects.filter(pk=business_id, del_flag=0).first()
        bra = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
        pra = ProjectRoleAllocation.objects.filter(pk=bra.project_role_alloc_id).first()
        if business:
            user_id = request.user.pk
            if usage and usage == '3':
                if role_alloc_id is None:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 复制编辑模板
                doc_ids = ProjectDocRole.objects.filter(project_id=business.cur_project_id, node_id=node_id,
                                                        role_id=pra.role_id, no=pra.no).values_list('doc_id',
                                                                                                    flat=True)
                project_docs = ProjectDoc.objects.filter(pk__in=doc_ids, usage=3)
                for doc in project_docs:
                    is_exists = BusinessDocContent.objects.filter(business_id=business_id, node_id=node_id,
                                                                  doc_id=doc.pk,
                                                                  business_role_allocation_id=role_alloc_id).exists()
                    if not is_exists:
                        path = business_template_save(business.pk, node_id, doc.name, doc.content)
                        BusinessDocContent.objects.create(business_id=business.pk, node_id=node_id, doc_id=doc.pk,
                                                          business_role_allocation_id=role_alloc_id, name=doc.name,
                                                          content=doc.content,
                                                          created_by=user_id, file_type=1, file=path)

            doc_list = get_business_templates(business, node_id, role_alloc_id, usage, pra)
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = doc_list
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_templates Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

# 个人笔记列表
def api_business_note_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id

        business = Business.objects.filter(pk=business_id).first()
        if business:
            project = Project.objects.get(pk=business.cur_project_id)
            nodes = FlowNode.objects.filter(flow_id=project.flow_id)

            note_list = []
            for item in nodes:
                note = BusinessNotes.objects.filter(business_id=business_id, node_id=item.id,
                                                      created_by_id=request.user.id, del_flag=0).first()
                can_edit = True if business.node_id == item.id else False
                if note:
                    note_dict = {'id': note.id, 'content': note.content}
                else:
                    note_dict = None

                note_list.append({
                    'node_id': item.id, 'node_name': item.name, 'note': note_dict,
                    'can_edit': can_edit
                })

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = note_list
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_note_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

# 创建实验笔记
def api_business_note_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.POST.get("business_id")  # 实验id
        node_id = request.POST.get("node_id")  # 环节id
        content = request.POST.get("content")  # 内容

        business = Business.objects.filter(pk=business_id).first()
        if business:
            # 验证实验环节是否在该环节
            if business.node_id == int(node_id):
                note, created = BusinessNotes.objects.update_or_create(business_id=business_id,
                                                                         node_id=node_id,
                                                                         created_by_id=request.user.id,
                                                                         defaults={'content': content})

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': note.id, 'content': note.content, 'node_id': note.node_id,
                    'business_id': note.business.id,
                    'created_by': user_simple_info(note.created_by.id)
                }
            else:
                resp = code.get_msg(code.BUSINESS_NODE_ERROR)
        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_note_create Exception:{0}'.format(str(e)))
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

# 实验文件展示列表
def api_business_file_display_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get('business_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        path_id = request.GET.get("path_id", None)  # 环节id

        business = Business.objects.filter(pk=business_id).first()
        if business:
            doc_list = get_business_display_files(business, node_id, path_id)
            # 分页信息
            paging = {
                'count': len(doc_list),
                'has_previous': False,
                'has_next': False,
                'num_pages': 1,
                'cur_page': 1,
            }
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': doc_list, 'paging': paging}

        else:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_business_file_display_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
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


# get unit user list for more business teammates configuration
def get_unit_userList(request):
    if request.session['login_type'] in [3, 5]:
        resp = auth_check(request, "POST")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            business_id = request.POST.get("business_id")
            business = Business.objects.get(id=business_id)

            targetUnitUsers = []
            if business.target_part is not None:
                targetUnitUsers = [{
                    'id': item.id,
                    'text': item.username,
                } for item in Tuser.objects.filter(tposition__parts_id=business.target_part.id, is_review=1)]
            elif business.target_company is not None:
                targetUnitUsers = [{
                    'id': item.id,
                    'text': item.username,
                } for item in Tuser.objects.filter(tcompany_id=business.target_company.id, is_review=1)]

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': targetUnitUsers}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_delete Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# get unit user list for more business teammates configuration
def add_more_teammates(request):
    if request.session['login_type'] in [3, 5]:
        resp = auth_check(request, "POST")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:

            business_id = request.POST.get("business_id")
            data = eval(request.POST.get("data"))
            for item in data:
                if item['role_name'] == '':
                    item['role_name'] = None
                else:
                    item['role_name'] = unicode(item['role_name'], "utf8")

            if len(TNotifications.objects.filter(type='businessMoreTeammate_' + business_id)) != 0:
                if teammates_configuration(business_id, data) == 'team_configured':
                    TNotifications.objects.filter(type='businessMoreTeammate_' + business_id).delete()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'success'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        except Exception as e:
            logger.exception('api_experiment_delete Exception:{0}'.format(str(e)))
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    else:
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节用户角色状态查询
def api_business_role_status(request):
    resp = auth_check(request, 'GET')
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.GET.get("business_id")  # 实验任务id
        node_id = request.GET.get("node_id")  # 环节id

        bus = Business.objects.filter(pk=business_id, del_flag=0).first()
        if bus is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=bus.cur_project_id)
        path = BusinessTransPath.objects.filter(business_id=business_id).last()
        node = FlowNode.objects.filter(pk=node_id, del_flag=0).first()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = get_all_roles_status(bus, project, node, path)
    except Exception as e:
        logger.exception('experiment_role_status Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_business_message_push(request):
    """
        实验发送消息
    """
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        business_id = request.POST.get("business_id", None)
        node_id = request.POST.get("node_id", None)
        alloc_role_id = request.POST.get("role_id", None)
        type = request.POST.get("type", None)
        msg = request.POST.get("msg", '')
        cmd = request.POST.get("cmd", None)
        param = request.POST.get("param", None)
        file_id = request.POST.get("file_id", None)
        data = request.POST.get('data', None)
        logger.info('business_id:%s,node_id:%s,role_id:%s,type:%s,cmd:%s,param:%s,file_id:%s,'
                    'data:%s' % (business_id, node_id, alloc_role_id, type, cmd, param, file_id, data))

        user = request.user

        if business_id is None or node_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        bus = Business.objects.filter(pk=business_id, del_flag=0).first()
        if bus is None:
            resp = code.get_msg(code.BUSINESS_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # todo 组长没有当前环节权限操作返回上一步提前结束等， 这里的判断是不是有问题
        # if exp.node_id != int(node_id):
        #     resp = code.get_msg(code.BUSINESS_NODE_ERROR)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        path = BusinessTransPath.objects.filter(business_id=business_id).last()
        if path is None:
            resp = code.get_msg(code.BUSINESS_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 是否有结束环节的权限
        can_terminate = get_role_node_can_terminate(bus, bus.cur_project_id, node_id, alloc_role_id)

        # 如果启动了表达管理，验证当前角色发言次数，每申请一次最多发言三次，
        # 如果是结束权限者则可发言
        role_status = BusinessRoleAllocationStatus.objects.filter(business_id=business_id, business_role_allocation_id=alloc_role_id, path_id=path.pk).first()
        logger.info('cmd:%s,control_status:%s,param:%s,type:%s' % (cmd, path.control_status, param, type))

        # if role_status is None:
        #     resp = code.get_msg(code.BUSINESS_NODE_ERROR)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if path.control_status == 2 and can_terminate is False:
            if type == const.MSG_TYPE_TXT or type == const.MSG_TYPE_AUDIO:
                if role_status.speak_times == 0:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if cmd == const.ACTION_DOC_SHOW:
                if role_status.show_status != 1:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if cmd == const.ACTION_DOC_SUBMIT:
                if role_status.submit_status != 1:
                    resp = code.get_msg(code.MESSAGE_SPEAKER_CONTROL)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 三期 - 根据上一步骤自动入席 判断是否入席
        bps = BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=path.id, business_role_allocation_id=alloc_role_id)
        if bps:
            business_position_status = bps.first()
            if business_position_status.sitting_status:  # 已入席
                role_status.sitting_status = const.SITTING_DOWN_STATUS

        name = request.user.name
        from_obj = str(request.user.pk)
        flow_role_id = FlowRoleAllocation.objects.get(id=role_status.business_role_allocation.flow_role_alloc_id).role_id
        role = BusinessRole.objects.filter(flow_role_id=flow_role_id, business_id=business_id).first()
        # 三期 组长没有权限也可以执行一些操作
        # 当前环节不存在该角色 除了组长
        if role is None:
            resp = code.get_msg(code.BUSINESS_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=bus.cur_project_id)
        node = FlowNode.objects.filter(pk=bus.node_id, del_flag=0).first()

        # 角色形象
        image = get_role_image(bus, role.image_id)
        if image is None:
            resp = code.get_msg(code.BUSINESS_ROLE_IMAGE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 角色占位
        pos = get_role_position(bus, project, node, path, role, alloc_role_id)

        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        opt = None
        if type == const.MSG_TYPE_TXT:
            if node.process.type == 1:
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 文本， 角色未入席不能说话
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            msg = msg.strip()
            if msg == '' or len(msg) > 30000:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            msg = tools.filter_invalid_str(msg)
            msg_obj = {'type': const.MSG_TYPE_TXT, 'msg': msg}
            ext = {'business_id': business_id, 'username': name,
                   'alloc_id': alloc_role_id, 'role_name': role.name, 'avatar': image['avatar'],
                   'cmd': const.ACTION_TXT_SPEAK, 'param': '', 'time': time, 'can_terminate': can_terminate,
                   'code_position': pos['code_position'] if pos else ''}

        elif type == const.MSG_TYPE_AUDIO:
            if pos is None:
                resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            # 音频
            if role_status.sitting_status == const.SITTING_UP_STATUS:
                resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if file_id is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            audio = BusinessMessageFile.objects.filter(pk=file_id).first()
            if audio is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            msg_obj = {'type': const.MSG_TYPE_AUDIO, 'url': (const.WEB_HOST + audio.file.url) if audio.file else '',
                       'filename': audio.file.name, 'length': audio.length, 'secret': ''}

            ext = {'business_id': business_id, 'username': name,
                   'alloc_id': alloc_role_id, 'role_name': role.name, 'avatar': image['avatar'],
                   'cmd': '', 'param': '', 'time': time, 'can_terminate': can_terminate,
                   'code_position': pos['code_position'] if pos else ''}

        elif type == const.MSG_TYPE_CMD:
            # 命令
            if cmd is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            result, opt = False, {}
            # 判断
            if cmd == const.ACTION_ROLE_BANNED:
                # 表达管理 data = {'control_status': 1}
                data = json.loads(data)
                result, opt = action_role_banned(bus, node_id, path.pk, data['control_status'])
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_MEET:
                # 约见
                result, opt = action_role_meet(bus, path.pk, role, alloc_role_id)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_APPLY_SPEAK:
                # 申请发言
                result, opt = True, {'role_id': alloc_role_id, 'role_name': role.name}
            elif cmd == const.ACTION_ROLE_APPLY_SPEAK_OPT:
                # 申请发言操作结果 data = {'msg_id':1,'role_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_role_speak_opt(bus, path.pk, data)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_DOC_APPLY_SHOW:
                # 申请展示
                result, opt = True, {'role_id': alloc_role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_REFRESH:
                # 刷新文件列表
                result, opt = True, {'role_id': alloc_role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_APPLY_SHOW_OPT:
                # 申请展示操作结果 data = {'msg_id':1,'doc_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_doc_apply_show_opt(bus, node_id, path.pk, data)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_DOC_SHOW:
                # 展示
                data = json.loads(data)
                result, opt = action_doc_show(data['doc_id'])
            elif cmd == const.ACTION_ROLE_LETOUT:
                # 送出 data [1, 2, 3, ...]
                role_ids = json.loads(data)
                result, lst = action_role_letout(bus, node, path.pk, role_ids)
                opt = {'data': lst}
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_LETIN:
                # 请入 data [1, 2, 3, ...]
                role_ids = json.loads(data)
                result, lst = action_role_letin(bus, node_id, path.pk, role_ids)
                opt = {'data': lst}
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_SITDOWN:
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 坐下
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_sitdown(bus, path.pk, role, pos, alloc_role_id)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_STAND:
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 起立
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_stand(bus, path.pk, role, pos, alloc_role_id)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_HIDE:
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 退席
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_hide(bus, node_id, path.pk, role, pos)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_ROLE_SHOW:
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 入席
                if role_status.sitting_status == const.SITTING_DOWN_STATUS:
                    resp = code.get_msg(code.BUSINESS_ROLE_HAS_IN_POSITION)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 占位状态
                position_status = ExperimentPositionStatus.objects.filter(business_id=bus.id, node_id=node_id,
                                                                          path_id=path.pk,
                                                                          position_id=pos['position_id'],
                                                                          sitting_status=const.SITTING_DOWN_STATUS).exists()
                if position_status:
                    resp = code.get_msg(code.BUSINESS_POSITION_HAS_USE)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_show(bus, node_id, path.pk, role, pos)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_DOC_APPLY_SUBMIT:
                # 申请提交
                result, opt = True, {'role_id': role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_APPLY_SUBMIT_OPT:
                # 申请提交操作结果 data = {'msg_id':1,'role_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_doc_apply_submit_opt(bus, node_id, path.pk, data)
                clear_cache(bus.pk)
            elif cmd == const.ACTION_DOC_SUBMIT:
                # 提交 实验文件id data = [1, 2, 3, ...]
                doc_ids = json.loads(data)
                result, lst = action_doc_submit(doc_ids)
                opt = {'data': lst}
            elif cmd == const.ACTION_EXP_RESTART:
                # 重新开始实验
                result, opt = action_exp_restart(exp, request.user.pk)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_EXP_BACK:
                # 返回上一步
                result, opt = action_exp_back(exp)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_EXP_NODE_END:
                # 结束环节 opt = {'next_node_id': 1, 'status': 1, 'process_type': 1},
                # data={'tran_id': 1, 'project_id': 0}
                data = json.loads(data)
                result, opt = action_exp_node_end(exp, role_id, data)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_EXP_FINISH:
                result, opt = action_exp_finish(exp, request.user.id)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_SUBMIT_EXPERIENCE:
                # 提交实验心得 data = {"content": ""}
                data = json.loads(data)
                result, opt = action_submit_experience(exp, data['content'], request.user.id)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
            elif cmd == const.ACTION_ROLE_VOTE:
                # 提交实验投票 data = {"status": 1}
                data = json.loads(data)
                result, opt = action_role_vote(exp, node_id, path, role_id, data['status'])
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_VOTE_END:
                # 提交实验投票结束 data = {}
                result, opt = action_role_vote_end(exp, node_id, path)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_REQUEST_SIGN:
                # 要求签字 data = {"doc_id": 1, "doc_name": "xxx", "role_id": 1, "role_name": "xx"}
                data = json.loads(data)
                result, opt = action_role_request_sign(exp, node_id, data)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
            elif cmd == const.ACTION_ROLE_SIGN:
                # 签字 data = {'msg_id':1,'result': 1,"doc_id": 1, "doc_name": 'xxx'}
                data = json.loads(data)
                sign = '{0}({1})'.format(request.user.name, role.name)
                result, opt = action_role_sign(exp, sign, node_id, role_id, data)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_SCHEDULE_REPORT:
                # 安排报告 data = {"role_id": 1, "role_name": "xx"}
                data = json.loads(data)
                result, opt = action_role_schedule_report(exp, node_id, path.pk, data)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")

            elif cmd == const.ACTION_ROLE_TOWARD_REPORT:
                # 走向发言席 data = {}
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_toward_report(exp, node_id, path.pk, role, pos)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_EDN_REPORT:
                # 走下发言席 data = {}
                if pos is None:
                    resp = code.get_msg(code.BUSINESS_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_end_report(exp, node_id, path.pk, role, pos)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLES_EXIT:
                # 退出实验 data = {}
                result, lst = action_roles_exit(exp, node, path.pk, request.user.id)
                opt = {'data': lst}
                clear_cache(exp.pk)
            elif cmd == const.ACTION_TRANS:
                result, opt = True, {}
            else:
                logger.info('action cmd %s' % cmd)
                resp = code.get_msg(code.MESSAGE_ACTION_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # if not result:
            #     raise Exception(opt)

            msg_obj = {'type': const.MSG_TYPE_TXT, 'msg': msg}
            ext = {'business_id': business_id, 'node_id': node_id, 'username': name,
                   'role_id': role_id, 'role_name': role.name, 'avatar': image['avatar'] if image else '',
                   'cmd': cmd, 'param': param, 'time': time, 'opt': opt, 'can_terminate': can_terminate,
                   'code_position': pos['code_position'] if pos else ''}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 保存消息，得到消息id
        user = request.user
        message = ExperimentMessage()
        if role_id:
            message = ExperimentMessage.objects.create(business_id=exp.pk, user_id=user.pk, role_id=role_id,
                                                       node_id=node_id, file_id=file_id, msg=msg, msg_type=type,
                                                       path_id=path.id, user_name=name, role_name=role.name,
                                                       ext=json.dumps(ext))
        ext['id'] = message.pk
        ext['opt_status'] = False

        flag, result = easemob.send_message(easemob.TARGET_TYPE_GROUP, msg_obj, from_obj, ext)
        logger.info('flag:%s, result:%s' % (flag, result))
        if flag:
            resp = code.get_msg(code.SUCCESS)
            if opt:
                resp['d'] = opt

            if can_terminate is False:
                # 角色发言次数减1
                if path.control_status == 2 and type != const.MSG_TYPE_CMD:
                    role_status.speak_times -= 1
                    role_status.save(update_fields=['speak_times'])
                    clear_cache(exp.pk)
        else:
            ExperimentMessage.objects.filter(pk=message.pk).delete()
            resp = code.get_msg(code.MESSAGE_SEND_FAILED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_message_push Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_business_report_generate(request):
    print "1"
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        business_id = request.GET.get("business_id")  # 实验ID
        user_id = request.GET.get("user_id", None)  # 用户
        user_id = user_id if user_id else request.user.id
        busi = Business.objects.filter(pk=business_id).first()
        print "2"
        if busi:
            print "3"
            # team = Team.objects.filter(pk=exp.team_id).first()
            project = Project.objects.filter(pk=busi.project_id).first()
            print "4"
            flow = Flow.objects.filter(pk=project.flow_id).first()
            print "5",business_id
            # members = BusinessTeamMember.objects.filter(business_id=business_id)
            # print members
            # course_class = CourseClass.objects.filter(pk=exp.course_class_id).first()

            # 小组成员
            # member_list = []
            # for uid in members:
            #     user = Tuser.objects.get(pk=uid)
            #     member_list.append(user.name)

            # # 组长
            # leader = Tuser.objects.filter(pk=team.leader).first()

            # 各环节提交文件信息和聊天信息
            paths = BusinessTransPath.objects.filter(business_id=busi.id)
            node_list = []
            for item in paths:
                node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first()
                doc_list = []
                vote_status = []
                if node.process.type == 2:
                    # 如果是编辑
                    # 应用模板
                    contents = BusinessDocContent.objects.filter(business_id=business_id, node_id=item.node_id,
                                                                   has_edited=True)
                    for d in contents:
                        doc_list.append({
                            'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                            'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                            'url': d.file.url if d.file else None
                        })
                    # 提交的文件
                    docs = BusinessDoc.objects.filter(business_id=business_id, node_id=item.node_id,
                                                        path_id=item.pk)
                    for d in docs:
                        sign_list = BusinessDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                            'signs': list(sign_list), 'url': d.file.url if d.file else None
                        })
                elif node.process.type == 3:
                    # 如果是展示
                    # 项目上传的文件
                    # project_docs = ProjectDoc.objects.filter(project_id=exp.project_id, usage=4)
                    # for d in project_docs:
                    #     doc_list.append({
                    #         'id': d.id, 'filename': d.name, 'signs': [],
                    #         'url': d.file.url, 'content': d.content, 'file_type': d.file_type,
                    #     })
                    project_docs = BusinessDoc.objects.filter(business_id=business_id, node_id=item.node_id,
                                                                path_id=item.pk)
                    for d in project_docs:
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'signs': [],
                            'url': d.file.url if d.file else None, 'content': d.content, 'file_type': d.file_type,
                        })
                        # docs = ExperimentDocContent.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                        #                                            has_edited=True)
                        # for d in docs:
                        #     doc_list.append({
                        #         'id': d.pk, 'filename': d.name, 'content': d.content,
                        #         'url': d.file.url if d.file else None, 'file_type': d.file_type,
                        #         'has_edited': d.has_edited, 'experiment_id': exp.pk, 'node_id': node.pk,
                        #         'role_name': '', 'node_name': node.name if node else None, 'created_by': None,
                        #         'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                        #     })
                # elif node.process.type == 5:
                #     # 如果是投票   三期 - 增加投票结果数量汇总
                #     vote_status_0_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                              node_id=item.node_id,
                #                                                              path_id=item.id, vote_status=0)
                #     vote_status_0 = []
                #     # 去掉老师观察者角色的数据
                #     for item0 in vote_status_0_temp:
                #         role_temp = ProjectRole.objects.filter(id=item0.role_id).first()
                #         if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #             vote_status_0.append(item0)
                #     vote_status_1_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                              node_id=item.node_id,
                #                                                              path_id=item.id, vote_status=1)
                #     vote_status_1 = []
                #     # 去掉老师观察者角色的数据
                #     for item1 in vote_status_1_temp:
                #         role_temp = ProjectRole.objects.filter(id=item1.role_id).first()
                #         if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #             vote_status_1.append(item1)
                #     vote_status_2_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                              node_id=item.node_id,
                #                                                              path_id=item.id, vote_status=2)
                #     vote_status_2 = []
                #     # 去掉老师观察者角色的数据
                #     for item2 in vote_status_2_temp:
                #         role_temp = ProjectRole.objects.filter(id=item2.role_id).first()
                #         if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #             vote_status_2.append(item2)
                #     vote_status_9_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                #                                                              node_id=item.node_id,
                #                                                              path_id=item.id, vote_status=9)
                #     vote_status_9 = []
                #     # 去掉老师观察者角色的数据
                #     for item9 in vote_status_9_temp:
                #         role_temp = ProjectRole.objects.filter(id=item9.role_id).first()
                #         if role_temp.name != const.ROLE_TYPE_OBSERVER:
                #             vote_status_9.append(item9)
                #     vote_status = [{'status': '同意', 'num': len(vote_status_1)},
                #                    {'status': '不同意', 'num': len(vote_status_2)},
                #                    {'status': '弃权', 'num': len(vote_status_9)},
                #                    {'status': '未投票', 'num': len(vote_status_0)}]
                #     pass
                else:
                    # 提交的文件
                    docs = BusinessDoc.objects.filter(business_id=business_id, node_id=item.node_id,
                                                        path_id=item.id)
                    for d in docs:
                        sign_list = BusinessDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'content': d.content,
                            'signs': list(sign_list), 'url': d.file.url if d.file else None, 'file_type': d.file_type
                        })
                # 消息
                # messages = BusinessMessage.objects.filter(business_id=business_id,
                #                                             node_id=item.node_id, path_id=item.id).order_by('timestamp')
                # message_list = []
                # for m in messages:
                #     audio = BusinessMessageFile.objects.filter(pk=m.file_id).first()
                #     message = {
                #         'user_name': m.user_name, 'role_name': m.role_name,
                #         'msg': m.msg, 'msg_type': m.msg_type, 'ext': json.loads(m.ext),
                #         'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                #     }
                #     if audio:
                #         message['url'] = const.WEB_HOST + audio.file.url
                #         message['filename'] = audio.file.name
                #         message['secret'] = ''
                #         message['length'] = audio.length
                #     message_list.append(message)

                # 个人笔记
                note = BusinessNotes.objects.filter(business_id=business_id,
                                                      node_id=item.node_id, created_by=user_id).first()
                node_list.append({
                    'docs': doc_list, 'id': node.id, 'node_name': node.name,
                    'note': note.content if note else None, 'type': node.process.type if node.process else 0,
                    'vote_status': vote_status
                })
            #     -------------------------------------------------------------------------------------------------------
            # experience = ExperimentExperience.objects.filter(business_id=busi.id, created_by=request.user.pk).first()
            # experience_data = {'status': 1, 'content': ''}
            # if experience:
            #     experience_data = {
            #         'id': experience.id, 'content': experience.content, 'status': experience.status,
            #         'created_by': user_simple_info(experience.created_by),
            #         'create_time': experience.create_time.strftime('%Y-%m-%d')
            #     }
            # ----------------------------------------------------------------------------------------------------------
            resp = code.get_msg(code.SUCCESS)
            # resp['d'] = {
            #     'name': u'{0} {1}'.format(busi.id, busi.name), 'project_name': project.name,
            #     'team_name': team.name, 'members': member_list, 'flow_name': flow.name,
            #     'finish_time': exp.finish_time.strftime('%Y-%m-%d') if exp.finish_time else None,
            #     'start_time': exp.start_time.strftime('%Y-%m-%d') if exp.start_time else None,
            #     'end_time': exp.end_time.strftime('%Y-%m-%d') if exp.end_time else None,
            #     'create_time': exp.create_time.strftime('%Y-%m-%d'),
            #     'leader_name': leader.name if leader else None,
            #     'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
            #                                           course_class.term) if course_class else None,
            #     'teacher': course_class.teacher1.name, 'nodes': node_list, 'experience': experience_data,
            # }
            resp['d'] = {
                'name': u'{0} {1}'.format(busi.id, busi.name), 'project_name': project.name,
                'flow_name': flow.name,
                'finish_time': busi.finish_time.strftime('%Y-%m-%d') if busi.finish_time else None,
                'start_time': busi.start_time.strftime('%Y-%m-%d') if busi.start_time else None,
                'end_time': busi.end_time.strftime('%Y-%m-%d') if busi.end_time else None,
                'create_time': busi.create_time.strftime('%Y-%m-%d'),
                'nodes': node_list
            }
            print node_list

        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_report_genetate Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
