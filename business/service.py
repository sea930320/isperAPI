#!/usr/bin/python
# -*- coding=utf-8 -*-

from business.models import *
import logging
from datetime import datetime

from account.service import user_simple_info
from django.db import transaction
from django.db.models import Q
from experiment.models import *
from course.models import CourseClass
from project.models import ProjectRole, Project, ProjectRoleAllocation, ProjectJump, ProjectDocRole, ProjectDoc
from team.models import Team, TeamMember
from utils import code, const, query, tools
from workflow.models import FlowRolePosition, FlowPosition, FlowNode, FlowTrans, RoleImage, RoleImageFile, \
    FlowProcess, ProcessAction, FlowDocs, FlowNodeDocs
from workflow.service import get_start_node
from django.core.cache import cache
from django.conf import settings
from docx import Document
import os
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage

logger = logging.getLogger(__name__)


def get_role_allocs_status_by_user(business, path, user):
    role_alloc_list = []
    btmQs = BusinessTeamMember.objects.filter(business=business, user=user)
    for btm in btmQs:
        try:
            roleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=path.node, role=btm.business_role,
                                                              no=btm.no, project_id=business.cur_project_id,
                                                              can_take_in=True).first()
            roleAllocStatus = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                                          business_role_allocation=roleAlloc).first()
            role_alloc_list.append({
                'alloc_id': roleAlloc.id, 'come_status': roleAllocStatus.come_status,
                'sitting_status': roleAllocStatus.sitting_status, 'stand_status': roleAllocStatus.stand_status,
                'vote_status': roleAllocStatus.vote_status, 'show_status': roleAllocStatus.show_status,
                'speak_times': 0 if path.control_status != 2 else roleAllocStatus.speak_times,
                'role': model_to_dict(roleAlloc.role), 'can_terminate': roleAlloc.can_terminate,
                'can_brought': roleAlloc.can_brought
            })
        except:
            continue
    return role_alloc_list


def get_all_simple_role_allocs_status(business, node, path):
    role_alloc_list = []
    btmQs = BusinessTeamMember.objects.filter(business=business)
    for btm in btmQs:
        try:
            roleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=node, role=btm.business_role,
                                                              no=btm.no, project_id=business.cur_project_id,
                                                              can_take_in=True).first()
            roleAllocStatus = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                                          business_role_allocation=roleAlloc).first()
            role_alloc_list.append({
                'alloc_id': roleAlloc.id, 'come_status': roleAllocStatus.come_status,
                'sitting_status': roleAllocStatus.sitting_status, 'stand_status': roleAllocStatus.stand_status,
                'vote_status': roleAllocStatus.vote_status, 'show_status': roleAllocStatus.show_status,
                'speak_times': 0 if path.control_status != 2 else roleAllocStatus.speak_times,
                'role': model_to_dict(roleAlloc.role), 'can_terminate': roleAlloc.can_terminate,
                'can_brought': roleAlloc.can_brought, 'role_name': roleAlloc.role.name, 'user_name': btm.user.name
            })
        except:
            continue
    return role_alloc_list

def get_role_allocs_status_simple_by_user(business, node, path, user_id):
    role__alloc_list = BusinessRoleAllocationStatus.objects.filter(business=business, business_role_allocation__node_id=node.pk,
                                                    path_id=path.pk,
                                                    user_id=user_id).values('business_role_allocation_id', 'sitting_status')
    data = list(role__alloc_list)
    return data

def get_user_with_node_on_business(business, user):
    nodes = []
    btmQs = BusinessTeamMember.objects.filter(business=business, user=user)
    for btm in btmQs:
        try:
            node_ids = BusinessRoleAllocation.objects.filter(business=business, role=btm.business_role,
                                                             no=btm.no, project_id=business.cur_project_id, can_take_in=True).values_list(
                'node_id', flat=True)
            nodes = list(FlowNode.objects.filter(id__in=node_ids).values_list('name', flat=True))
        except Exception as e:
            logger.exception(u'get_user_with_node_on_business Exception:{}'.format(str(e)))
            continue
    return nodes


def get_business_detail(business):
    project = Project.objects.filter(pk=business.cur_project_id).first()
    team_dict = [model_to_dict(member) for member in BusinessTeamMember.objects.filter(business=business, del_flag=0)]
    # 项目信息

    if project:
        project_dict = {
            'id': project.id, 'name': project.name,
            'office_item': project.officeItem.name if project.officeItem else None
        }
    else:
        project_dict = None

    node = FlowNode.objects.filter(pk=business.node_id).first() if business.node else None
    if node:
        process = node.process
        cur_node = {
            'id': node.id, 'name': node.name, 'condition': node.condition, 'process_type': process.type,
            'can_switch': process.can_switch
        }
    else:
        cur_node = None
    role_allocs = []
    business_role_allocs = BusinessRoleAllocation.objects.filter(business=business, project_id=business.cur_project_id, can_take_in=True)
    for bra in business_role_allocs:
        try:
            teamMember = BusinessTeamMember.objects.filter(business=business, del_flag=0,
                                                           project_id=business.cur_project_id, business_role=bra.role,
                                                           no=bra.no).first()
        except:
            teamMember = None
        role_allocs.append({
            'id': bra.id, 'name': bra.role.name, 'type': bra.role.type,
            'user_id': teamMember.user_id if teamMember else None
        })
    data = {
        'id': business.id, 'show_nickname': business.show_nickname, 'entire_graph': project.entire_graph,
        'status': business.status, 'flow_id': project.flow_id,
        'start_time': business.start_time.strftime('%Y-%m-%d') if business.start_time else None,
        'end_time': business.end_time.strftime('%Y-%m-%d') if business.end_time else None,
        'create_by': user_simple_info(business.created_by_id), 'node_id': business.node_id,
        'create_time': business.create_time.strftime('%Y-%m-%d'), 'team': team_dict,
        'name': u'{0} {1}'.format(business.id, business.name),
        'project': project_dict, 'node': cur_node, 'huanxin_id': business.huanxin_id,
        'role_allocs': role_allocs
    }
    return data


def get_business_pre_node_path(business):
    try:
        cur_path = BusinessTransPath.objects.filter(business=business,
                                                    node_id=business.node_id).last()
        if cur_path is None:
            return None
        if cur_path.step == 1:
            return None
        pre_path = BusinessTransPath.objects.filter(business=business,
                                                    step__lt=cur_path.step).last()
        if pre_path is None:
            return None
        return pre_path
    except Exception as e:
        logger.exception(u'get_business_pre_node_path Exception:{}'.format(str(e)))
        return None

def get_node_path_messages_on_business(business, node_id, path_id, is_paging, page, size):
    """
    环节消息
    """
    if is_paging == 1:
        sql = '''SELECT t.id,t.user_id `from`,t.msg_type,t.msg `data`,t.ext,t.file_id,t.opt_status
        from t_business_message t WHERE t.business_id=%s and t.node_id=%s and t.path_id=%s
        order by timestamp desc''' % (business.pk, node_id, path_id)
        count_sql = '''SELECT count(t.id) from t_ebusiness_message t
        WHERE t.business_id=%s and t.node_id=%s and t.path_id=%s''' % (business.pk, node_id, path_id)
        logger.info(sql)
        data = query.pagination_page(sql, ['id', 'from', 'msg_type', 'data', 'ext', 'file_id', 'opt_status'],
                                     count_sql, page, size)
        return data
    else:
        sql = '''SELECT t.id,t.user_id `from`,t.msg_type,t.msg `data`,t.ext,t.file_id,t.opt_status
        from t_business_message t WHERE t.business_id=%s and t.node_id=%s and t.path_id=%s
        order by timestamp asc''' % (business.pk, node_id, path_id)
        logger.info(sql)
        data = query.select(sql, ['id', 'from', 'msg_type', 'data', 'ext', 'file_id', 'opt_status'])
        return {'results': data, 'paging': None}