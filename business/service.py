#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
from business.models import *
import logging
from datetime import datetime

from account.service import user_simple_info
from django.db import transaction
from django.db.models import Q
from project.models import ProjectRole, Project, ProjectRoleAllocation, ProjectJump, ProjectDocRole, ProjectDoc
from team.models import Team, TeamMember
from utils import code, const, query, tools
from workflow.models import FlowRolePosition, FlowPosition, FlowNode, FlowTrans, RoleImage, RoleImageFile, \
    FlowProcess, ProcessAction, FlowDocs, FlowNodeDocs, FlowRoleAllocation
from workflow.service import get_start_node
from django.core.cache import cache
from django.conf import settings
from docx import Document
import os
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage

logger = logging.getLogger(__name__)


def set_cache_keys(experiment_id, item):
    """
    保存缓存key列表
    """
    pass
    # try:
    #     key = tools.make_key(const.CACHE_EXPERIMENT_KEYS, experiment_id, 1)
    #     data = cache.get(key)
    #     if data:
    #         if item not in data:
    #             data.append(item)
    #     else:
    #         data = [item]
    #         cache.set(key, data)
    # except Exception as e:
    #     logger.exception(u'set_cache_keys Exception:{}'.format(str(e)))


def clear_cache(experiment_id):
    pass
    """
    清除缓存
    """
    # cache.clear()
    # try:
    #     key = tools.make_key(const.CACHE_EXPERIMENT_KEYS, experiment_id, 1)
    #     data = cache.get(key)
    #     cache.delete_many(data)
    #     cache.delete(key)
    # except Exception as e:
    #     logger.exception(u'set_cache_keys Exception:{}'.format(str(e)))


def get_role_allocs_status_by_user(business, path, user):
    role_alloc_list = []
    if path.node.parallel_node_start == 0:
        btmQs = BusinessTeamMember.objects.filter(business=business, project_id=business.cur_project_id, user=user)
        for btm in btmQs:
            try:
                roleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=path.node, role=btm.business_role,
                                                                  no=btm.no, project_id=business.cur_project_id,
                                                                  can_take_in=True).first()
                roleAllocStatus = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                                              business_role_allocation=roleAlloc).first()
                role_alloc_list.append({
                    'alloc_id': roleAlloc.id, 'come_status': roleAllocStatus.come_status, 'no': roleAlloc.no,
                    'sitting_status': roleAllocStatus.sitting_status, 'stand_status': roleAllocStatus.stand_status,
                    'vote_status': roleAllocStatus.vote_status, 'show_status': roleAllocStatus.show_status,
                    'speak_times': 0,
                    'role': model_to_dict(roleAlloc.role), 'can_terminate': roleAlloc.can_terminate,
                    'can_brought': roleAlloc.can_brought
                })
            except:
                continue
    elif path.node.parallel_node_start == 1:
        btmQs = BusinessTeamMember.objects.filter(business=business, project_id=business.cur_project_id, user=user)
        for pn in business.parallel_nodes.all():
            if pn.node.is_parallel_merging == 0 or \
                    (pn.node.is_parallel_merging == 1 and business.parallel_passed_nodes.filter(node__task_id__in=FlowTrans.objects.filter(outgoing=pn.node.task_id).values_list('incoming', flat=True)).count() == FlowTrans.objects.filter(outgoing=pn.node.task_id).count()):
                node_alloc_list = []
                for btm in btmQs:
                    try:
                        roleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=pn.node, role=btm.business_role,
                                                                          no=btm.no, project_id=business.cur_project_id,
                                                                          can_take_in=True).first()
                        roleAllocStatus = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                                                      business_role_allocation=roleAlloc).first()
                        node_alloc_list.append({
                            'alloc_id': roleAlloc.id, 'come_status': roleAllocStatus.come_status, 'no': roleAlloc.no,
                            'sitting_status': roleAllocStatus.sitting_status, 'stand_status': roleAllocStatus.stand_status,
                            'vote_status': roleAllocStatus.vote_status, 'show_status': roleAllocStatus.show_status,
                            'speak_times': 0,
                            'role': model_to_dict(roleAlloc.role), 'can_terminate': roleAlloc.can_terminate,
                            'can_brought': roleAlloc.can_brought
                        })
                    except:
                        continue
                role_alloc_list.append(node_alloc_list)
    return role_alloc_list


def get_all_simple_role_allocs_status(business, node):
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
                'speak_times': 0,
                'role': model_to_dict(roleAlloc.role), 'can_terminate': roleAlloc.can_terminate,
                'can_brought': roleAlloc.can_brought, 'role_name': roleAlloc.role.name, 'user_name': btm.user.name
            })
        except:
            continue
    return role_alloc_list


def get_role_allocs_status_simple_by_user(business, node, path, user_id):
    role_alloc_list = []
    btmQs = BusinessTeamMember.objects.filter(business=business, user_id=user_id)
    for btm in btmQs:
        try:
            roleAlloc = BusinessRoleAllocation.objects.filter(business=business, node=node, role=btm.business_role,
                                                              no=btm.no, project_id=business.cur_project_id,
                                                              can_take_in=True).first()
            roleAllocStatus = BusinessRoleAllocationStatus.objects.filter(business=business,
                                                                          business_role_allocation=roleAlloc).first()
            role_alloc_list.append({
                'business_role_allocation_id': roleAllocStatus.business_role_allocation_id,
                'sitting_status': roleAllocStatus.sitting_status,
            })
        except:
            continue
    return role_alloc_list


def get_user_with_node_on_business(business, user):
    nodes = []
    btmQs = BusinessTeamMember.objects.filter(business=business, project_id=business.cur_project_id, user=user)
    for btm in btmQs:
        try:
            node_ids = BusinessRoleAllocation.objects.filter(business=business, role=btm.business_role,
                                                             no=btm.no, project_id=business.cur_project_id,
                                                             can_take_in=True).values_list(
                'node_id', flat=True)
            nodes = list(FlowNode.objects.filter(id__in=node_ids).values_list('name', flat=True))
        except Exception as e:
            logger.exception(u'get_user_with_node_on_business Exception:{}'.format(str(e)))
            continue
    return nodes


def get_business_detail(business):
    project = Project.objects.filter(pk=business.cur_project_id).first()
    team_dict = [{
        'id': member.user_id,
        'name': member.user.name if member.user is not None else '',
        'username': member.user.username if member.user is not None else '',
        'type': member.user.type if member.user is not None else '',
        'gender': member.user.gender if member.user is not None else '',
        'position': model_to_dict(member.user.tposition) if member.user is not None and member.user.tposition else None
    } for member in
        BusinessTeamMember.objects.filter(business=business, project_id=business.cur_project_id, del_flag=0)]
    # 项目信息

    if project:
        project_dict = {
            'id': project.id, 'name': project.name,
            'office_item': project.officeItem.name if project.officeItem else None,
            'office_item_id': project.officeItem.id if project.officeItem else None,
        }
    else:
        project_dict = None

    node = FlowNode.objects.filter(pk=business.node_id).first() if business.node else None
    if node:
        if node.parallel_node_start == 0:
            process = node.process
            if process.type == 11:
                bSurvey = BusinessSurvey.objects.filter(business_id=business.id, project_id=business.cur_project_id,
                                                        node_id=node.id, target__in=[0, 1]).first()
                if bSurvey:
                    allocations = BusinessRoleAllocation.objects.filter(business_id=business.id,
                                                                        project_id=business.cur_project_id, node_id=node.id)
                    allocations.update(can_take_in=True)
            cur_node = {
                'id': node.id, 'name': node.name, 'condition': node.condition, 'process_type': process.type,
                'can_switch': process.can_switch
            }
        else:
            cur_node = []
            for subNode in business.parallel_nodes.all():
                process = subNode.node.process
                if process.type == 11:
                    bSurvey = BusinessSurvey.objects.filter(business_id=business.id, project_id=business.cur_project_id,
                                                            node_id=subNode.node.id, target__in=[0, 1]).first()
                    if bSurvey:
                        allocations = BusinessRoleAllocation.objects.filter(business_id=business.id,
                                                                            project_id=business.cur_project_id, node_id=subNode.node.id)
                        allocations.update(can_take_in=True)
                if subNode.node.is_parallel_merging == 0:
                    cur_node.append({
                        'id': subNode.node.id, 'name': subNode.node.name, 'condition': subNode.node.condition, 'process_type': process.type,
                        'can_switch': process.can_switch
                    })
                elif subNode.node.is_parallel_merging == 1 and \
                        business.parallel_passed_nodes.filter(node__task_id__in=FlowTrans.objects.filter(outgoing=subNode.node.task_id).values_list('incoming', flat=True)).count() == FlowTrans.objects.filter(outgoing=subNode.node.task_id).count():
                    cur_node.append({
                        'id': subNode.node.id, 'name': subNode.node.name, 'condition': subNode.node.condition, 'process_type': process.type,
                        'can_switch': process.can_switch
                    })
    role_allocs = []
    business_role_allocs = BusinessRoleAllocation.objects.filter(business=business, project_id=business.cur_project_id,
                                                                 can_take_in=True)
    for bra in business_role_allocs:
        image = get_role_image(bra.flow_role_alloc_id)
        try:
            teamMember = BusinessTeamMember.objects.filter(business=business, del_flag=0,
                                                           project_id=business.cur_project_id, business_role=bra.role,
                                                           no=bra.no).first()
        except:
            teamMember = None
        role_allocs.append({
            'id': bra.id, 'name': bra.role.name, 'type': bra.role.type,
            'node_id': bra.node_id,
            'user_id': teamMember.user_id if teamMember else None,
            'user_name': teamMember.user.name if teamMember and teamMember.user is not None else None,
            'image': image,
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
        'role_allocs': role_allocs,
        'company': model_to_dict(business.target_company, fields=['id',
                                                                  'name']) if business.target_company_id else model_to_dict(
            business.target_part.company, fields=['id',
                                                  'name']) if business.target_part_id else None
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
        from t_business_message t
        LEFT JOIN t_business_role_allocation r on t.business_role_allocation_id = r.id 
        WHERE t.business_id=%s and r.node_id=%s and t.path_id=%s
        order by timestamp desc''' % (business.pk, node_id, path_id)
        count_sql = '''SELECT count(t.id) from t_business_message t
        LEFT JOIN t_business_role_allocation r on t.business_role_allocation_id = r.id 
        WHERE t.business_id=%s and r.node_id=%s and t.path_id=%s''' % (business.pk, node_id, path_id)
        logger.info(sql)
        data = query.pagination_page(sql, ['id', 'from', 'msg_type', 'data', 'ext', 'file_id', 'opt_status'],
                                     count_sql, page, size)
        return data
    else:
        sql = '''SELECT t.id,t.user_id `from`,t.msg_type,t.msg `data`,t.ext,t.file_id,t.opt_status
        from t_business_message t
        LEFT JOIN t_business_role_allocation r on t.business_role_allocation_id = r.id
        WHERE t.business_id=%s and r.node_id=%s and t.path_id=%s
        order by timestamp asc''' % (business.pk, node_id, path_id)
        logger.info(sql)
        data = query.select(sql, ['id', 'from', 'msg_type', 'data', 'ext', 'file_id', 'opt_status'])
        print data
        return {'results': data, 'paging': None}


def get_role_alloc_process_actions(business, path, role_id, process_action_ids):
    process_actions = ProcessAction.objects.filter(id__in=process_action_ids,
                                                   del_flag=0).values('id', 'name', 'cmd')

    data = list(process_actions)
    return data


def get_node_role_alloc_docs(business, node_id, project_id, flow_id, role_alloc_id):
    # 角色项目素材
    cur_doc_list = []
    operation_guide_list = []
    project_tips_list = []

    # 流程素材，对所有角色
    doc_ids = FlowNodeDocs.objects.filter(flow_id=flow_id, node_id=node_id, del_flag=0).values_list('doc_id',
                                                                                                    flat=True)
    if doc_ids:
        node_docs = FlowDocs.objects.filter(id__in=doc_ids, usage__in=(1, 2, 3))
        for item in node_docs:
            url = ''
            if item.file:
                url = item.file.url
            if item.usage == 1:
                logger.info(item.name)
                operation_guide_list.append({
                    'id': item.id, 'name': item.name, 'type': item.type, 'usage': item.usage,
                    'content': item.content,
                    'url': url, 'file_type': item.file_type
                })
            else:
                cur_doc_list.append({
                    'id': item.id, 'name': item.name, 'type': item.type, 'usage': item.usage,
                    'content': item.content,
                    'url': url, 'file_type': item.file_type
                })
    data = {'cur_doc_list': cur_doc_list, 'operation_guides': operation_guide_list,
            'project_tips_list': project_tips_list}
    return data


def get_pre_node_role_alloc_docs(business, node_id, project_id, role_alloc_id):
    data = []
    node_ids = list(BusinessTransPath.objects.filter(business_id=business.id).values_list('node_id', flat=True))
    businessRoleAlloc = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
    if not businessRoleAlloc:
        return []
    projectRoleAlloc = ProjectRoleAllocation.objects.filter(pk=businessRoleAlloc.project_role_alloc_id).first()
    if not projectRoleAlloc:
        return []

    if node_ids:
        node_ids.remove(business.node_id)
        doc_ids = ProjectDocRole.objects.filter(project_id=project_id, node_id__in=node_ids,
                                                role_id=projectRoleAlloc.role_id, no=projectRoleAlloc.no).values_list(
            'doc_id', flat=True)
        project_docs = ProjectDoc.objects.filter(id__in=doc_ids)
        for item in project_docs:
            if item.usage in [2, 3, 4, 5, 7]:
                data.append({
                    'id': item.id, 'name': item.name, 'type': item.type, 'usage': item.usage,
                    'content': item.content, 'url': item.file.url, 'file_type': item.file_type
                })
    return data


def business_template_save(business_id, node_id, name, content):
    """
    保存应用模板生成文件
    :param content: 内容
    :param doc_id: 模板id
    :return:
    """
    path = ''
    try:
        # 打开文档
        document = Document()
        # 添加文本
        document.add_paragraph(content)
        # 保存文件
        media = settings.MEDIA_ROOT
        path = u'{}/business/{}'.format(media, business_id)
        is_exists = os.path.exists(path)
        if not is_exists:
            os.makedirs(path)
        media_path = u'{}/{}-{}'.format(path, node_id, name)
        logger.info(media_path)
        document.save(media_path)

        path = u'business/{}/{}-{}'.format(business_id, node_id, name)
    except Exception as e:
        logger.exception(u'business_template_save Exception:{}'.format(str(e)))
    return path


# modified by ser -- edit_module param is added
def get_business_templates(business, node_id, role_alloc_id, usage, pra=None, edit_module=None):
    doc_list = []
    try:

        """
        实验模板
        """
        if role_alloc_id and role_alloc_id != 'observable' and pra is None :
            bra = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
            pra = ProjectRoleAllocation.objects.filter(pk=bra.project_role_alloc_id).first()

        if usage and usage == '3':
            if edit_module is None:
                if role_alloc_id == 'observable':
                    docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id)
                else:
                    docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id,
                                                         business_role_allocation_id=role_alloc_id)
            else:
                docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id)

            for item in docs:
                doc_list.append({
                    'id': item.id, 'name': item.name, 'type': '', 'usage': 3,
                    'content': item.content, 'file_type': item.file_type,
                    'has_edited': item.has_edited, 'from': 1,
                    'sign_status': item.sign_status, 'sign': item.sign,
                    'role_alloc_id': item.business_role_allocation_id, 'url': item.file.url
                })
        else:
            # modified by ser -- edit_module validation
            if role_alloc_id and edit_module is None:
                doc_ids = ProjectDocRole.objects.filter(project_id=business.cur_project_id, node_id=node_id,
                                                        role_id=pra.role_id, no=pra.no).values_list('doc_id', flat=True)
            else:
                doc_ids = ProjectDocRole.objects.filter(project_id=business.cur_project_id,
                                                        node_id=node_id).values_list('doc_id', flat=True)
            qs = ProjectDoc.objects.filter(project_id=business.cur_project_id)
            if usage:
                qs = qs.filter(usage=usage)
            print qs
            if node_id:
                qs = qs.filter(id__in=doc_ids)
            print qs
            for item in qs:
                doc_list.append({
                    'id': item.id, 'name': item.name, 'type': item.type, 'usage': item.usage,
                    'content': item.content, 'file_type': item.file_type,
                    'has_edited': False, 'from': 1,
                    'sign_status': 0,
                    'sign': '',
                    'role_alloc_id': None,
                    'url': item.file.url
                })

            # 三期改bug增加------流程素材，对所有角色----------我也不知道对不对 测试说要加我就加了呗
            # 一会儿流程素材一会儿项目素材的
            # 我也搞不懂了，这几行代码还是先注掉吧
            doc_ids = FlowNodeDocs.objects.filter(node_id=node_id, del_flag=0).values_list('doc_id', flat=True)
            if doc_ids:
                node_docs = FlowDocs.objects.filter(id__in=doc_ids, usage=usage)
                for item in node_docs:
                    url = ''
                    if item.file:
                        url = item.file.url
                    doc_list.append({
                        'id': item.id, 'name': item.name, 'type': item.type, 'usage': item.usage,
                        'content': item.content, 'file_type': item.file_type,
                        'has_edited': False, 'from': 1,
                        'sign_status': 0,
                        'sign': '',
                        'role_alloc_id': None,
                        'url': url
                    })
    except Exception as e:
        logger.exception('get_business_templates Exception:{0}'.format(str(e)))
    return doc_list


def get_role_alloc_node_can_terminate(business, project_id, node_id, role_alloc_id):
    if BusinessRoleAllocation.objects.filter(
            pk=role_alloc_id,
            project_id=project_id,
            can_terminate=True).exists():
        can_terminate = True
    else:
        can_terminate = False
    return can_terminate


def get_role_alloc_position(business, project, node, path, bra):
    try:
        fra = FlowRoleAllocation.objects.filter(bra.flow_role_alloc_id, del_flag=0).first()
        role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node.pk,
                                                        role_id=fra.role_id, no=fra.no, del_flag=0).first()
        pos = None
        if role_position:
            pos = FlowPosition.objects.filter(pk=role_position.position_id, del_flag=0).first()

        # 判断是否存在报告席，是否已走向报告
        report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE,
                                                 del_flag=0).first()
        if report_pos:
            report_exists = BusinessReportStatus.objects.filter(business_id=business.pk, business_role_allocation=bra,
                                                                path_id=path.pk,
                                                                schedule_status=const.SCHEDULE_UP_STATUS).exists()
            if report_exists:
                pos = report_pos
        if pos:
            data = {'position_id': pos.id, 'org_position_id': role_position.position_id,
                    'code_position': pos.code_position, 'position': pos.position,
                    'actor1': pos.actor1, 'actor2': pos.actor2, 'type': pos.type}
            return data
        else:
            return None
    except Exception as e:
        logger.exception('get_role_alloc_position Exception:{0}'.format(str(e)))
        return None


def check_jump_project(project):
    """
    实验是否可以开始（所有小组成员均分配角色，角色全部分配）
    :param exp: 实验对象
    :return:
    """
    flag = True
    jump_process = FlowProcess.objects.filter(type=const.PROCESS_JUMP_TYPE,
                                              del_flag=const.DELETE_FLAG_NO).first()
    if jump_process:
        jumps = FlowNode.objects.filter(flow_id=project.flow_id, process=jump_process,
                                        del_flag=const.DELETE_FLAG_NO).count()
        if jumps > 0:
            count = ProjectJump.objects.filter(project_id=project.pk).count()
            if jumps > count:
                flag = False
    return flag


def get_all_roles_status(bus, project, node, path):
    """
    所有角色
    """
    # key = tools.make_key(const.CACHE_ALL_ROLES_STATUS, '%s:%s:%s' % (bus.pk, node.pk, path.pk), 1)
    # set_cache_keys(bus.pk, key)
    # data = cache.get(key)
    # if data:
    #     return data
    # else:
    # 报告席
    report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()
    report_status = BusinessReportStatus.objects.filter(business_id=bus.pk, business_role_allocation__node_id=node.pk,
                                                        path_id=path.pk,
                                                        schedule_status=const.SCHEDULE_UP_STATUS).first()

    sql = '''SELECT a.id, a.role_id, a.no, t.come_status, t.sitting_status, t.stand_status, t.vote_status,
            t.show_status,t.speak_times,r.`name` role_name,r.flow_role_id,u.name,f.image_id,i.gender
            from t_business_role_allocation_status t
            LEFT JOIN t_business_role_allocation a ON t.business_role_allocation_id=a.id
            LEFT JOIN t_business_role r ON a.role_id=r.id
            LEFT JOIN t_flow_role_allocation f ON a.flow_role_alloc_id=f.id
            LEFT JOIN t_business_team_member m ON a.no=m.no AND a.role_id=m.business_role_id
            LEFT JOIN t_user u ON m.user_id=u.id
            LEFT JOIN t_role_image i ON i.id=f.image_id
            WHERE t.business_id=%s and a.node_id=%s''' % (bus.pk, node.pk)
    sql += ' order by t.sitting_status '
    role_list = query.select(sql, ['alloc_id', 'role_id', 'no', 'come_status', 'sitting_status', 'stand_status',
                                   'vote_status', 'show_status', 'speak_times', 'role_name', 'flow_role_id',
                                   'user_name', 'image_id', 'gender'])
    for i in range(0, len(role_list)):
        role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node.pk,
                                                        role_id=role_list[i]['flow_role_id'],
                                                        no=role_list[i]['no']).first()
        actors = []
        if role_position:
            qs_files = RoleImageFile.objects.filter(image_id=role_list[i]['image_id'])
            if report_pos and report_status:
                if role_list[i]['alloc_id'] == report_status.business_role_allocation_id:
                    if report_pos.actor1:
                        actor1 = qs_files.filter(direction=report_pos.actor1).first()
                        actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
                    if report_pos.actor2:
                        actor2 = qs_files.filter(direction=report_pos.actor2).first()
                        actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')
                    position = {'id': report_pos.id, 'position': report_pos.position,
                                'code_position': report_pos.code_position}
                else:
                    pos = FlowPosition.objects.filter(pk=role_position.position_id).first()
                    if pos:
                        if pos.actor1:
                            actor1 = qs_files.filter(direction=pos.actor1).first()
                            actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
                        if pos.actor2:
                            actor2 = qs_files.filter(direction=pos.actor2).first()
                            actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')
                        position = {'id': pos.id, 'position': pos.position, 'code_position': pos.code_position}
                    else:
                        position = None
            else:
                pos = FlowPosition.objects.filter(pk=role_position.position_id).first()
                if pos:
                    if pos.actor1:
                        actor1 = qs_files.filter(direction=pos.actor1).first()
                        actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
                    if pos.actor2:
                        actor2 = qs_files.filter(direction=pos.actor2).first()
                        actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')
                    position = {'id': pos.id, 'position': pos.position, 'code_position': pos.code_position}
                else:
                    position = None
        else:
            position = None
        role_list[i]['position'] = position
        role_list[i]['actors'] = actors
        # clear_cache(bus.pk)key, role_list)
    return role_list


def get_role_node_can_terminate(bus, project_id, node_id, role_alloc_id):
    try:
        if BusinessRoleAllocation.objects.filter(project_id=project_id, node_id=node_id, id=role_alloc_id,
                                                 can_terminate=True).exists():
            can_terminate = True
        else:
            can_terminate = False
        return can_terminate
    except Exception as e:
        logger.exception('get_role_node_can_terminate Exception:{0}'.format(str(e)))
        return False


def get_role_image(fra_id):
    image_id = FlowRoleAllocation.objects.get(pk=fra_id).image_id
    try:
        image = RoleImage.objects.filter(pk=image_id).first()
        if image:
            data = {'image_id': image.pk, 'name': image.name, 'gender': image.gender,
                    'avatar': image.avatar.url if image.avatar else ''}
            return data
        else:
            return None
    except Exception as e:
        logger.exception('get_role_image Exception:{0}'.format(str(e)))
        return None


def get_role_position(bus, project, node, role, role_alloc_id):
    try:
        bra = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
        fra = FlowRoleAllocation.objects.filter(pk=bra.flow_role_alloc_id).first()
        role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node.pk,
                                                        role_id=fra.role_id, no=fra.no, del_flag=0).first()
        pos = None
        if role_position:
            pos = FlowPosition.objects.filter(pk=role_position.position_id, del_flag=0).first()

        # 判断是否存在报告席，是否已走向报告
        report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE,
                                                 del_flag=0).first()
        if report_pos:
            report_exists = BusinessReportStatus.objects.filter(business_id=bus.pk,
                                                                business_role_allocation_id=role_alloc_id,
                                                                # path_id=path.pk,
                                                                schedule_status=const.SCHEDULE_UP_STATUS).exists()
            if report_exists:
                pos = report_pos
        if pos:
            data = {'position_id': pos.id, 'org_position_id': role_position.position_id,
                    'code_position': pos.code_position, 'position': pos.position,
                    'actor1': pos.actor1, 'actor2': pos.actor2, 'type': pos.type}
            return data
        else:
            return None
    except Exception as e:
        logger.exception('get_role_position Exception:{0}'.format(str(e)))
        return None


def action_role_banned(bus, node_id, path_id, control_status):
    """
    表达管理
    :param control_status:  表达管理状态：1，未启动；2，已启动
    :param exp: 实验
    :return:
    """
    try:
        BusinessTransPath.objects.filter(pk=bus.path_id).update(control_status=control_status)
        if control_status == 2:
            BusinessRoleAllocationStatus.objects.filter(
                business_id=bus.id,
                business_role_allocation__node_id=node_id,
                # path_id=path_id
            ).update(speak_times=0, show_status=9,submit_status=9)
        opt = {'control_status': control_status}
        return True, opt
    except Exception as e:
        logger.exception(u'action_role_banned Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_meet(bus, path_id, role, role_alloc_id):
    """
    申请约见
    :param role_id: 角色id
    :param node_id: 环节id
    :param exp: 实验
    :return:
    """
    try:
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).update(come_status=1, stand_status=2)

        role_info = {'id': role_alloc_id, 'name': role.name}
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_meet Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_speak_opt(bus, path_id, data):
    """
    申请发言操作结果
    :param exp: 实验
    :param node_id: 环节id
    :param role_id: 角色id
    :param is_pass: 是否同意: 1,同意；2，不同意
    :return:
    """
    try:
        if 'msg_id' in data.keys():
            BusinessMessage.objects.filter(pk=data['msg_id']).update(opt_status=True)
        alloc_role_status = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            # path_id=path_id,
            business_role_allocation_id=data['role_alloc_id']
        ).first()
        if alloc_role_status and int(data['result']) == 1:
            alloc_role_status.speak_times = const.MESSAGE_MAX_TIMES
            alloc_role_status.save(update_fields=['speak_times'])
        role = BusinessRoleAllocation.objects.get(pk=data['role_alloc_id']).role
        return True, {'role_id': data['role_alloc_id'], 'role_name': role.name, 'result': data['result']}
    except Exception as e:
        logger.exception(u'action_role_speak_opt Exception:{}'.format(str(e)))
        return False, str(e)


def action_doc_apply_show_opt(bus, node_id, path_id, data):
    """
    申请展示操作结果
    :param exp: 实验
    :param node_id: 环节id
    :param role_id: 角色id
    :param is_pass: 是否同意: 1,同意；2，不同意
    :return:
    """
    try:
        if 'msg_id' in data.keys():
            BusinessMessage.objects.filter(pk=data['msg_id']).update(opt_status=True)
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            # path_id=path_id,
            business_role_allocation_id=data['role_alloc_id']
        ).update(show_status=data['result'])
        role = BusinessRoleAllocation.objects.get(pk=data['role_alloc_id']).role
        return True, {'role_id': data['role_alloc_id'], 'role_name': role.name, 'result': data['result']}
    except Exception as e:
        logger.exception(u'action_doc_apply_show_opt Exception:{}'.format(str(e)))
        return False, str(e)


def action_doc_show(doc_id):
    """
    展示
    :return:
    """
    try:
        if doc_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return False, resp
        doc = BusinessDoc.objects.filter(pk=doc_id).first()
        data = {
            'id': doc.id, 'name': doc.filename, 'url': doc.file.url, 'file_type': doc.file_type
        }
        return True, data
    except Exception as e:
        logger.exception(u'action_role_apply_show Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_letout(bus, node, path_id, role_alloc_ids):
    """
    送出
    :return:
    """
    try:
        with transaction.atomic():
            BusinessRoleAllocationStatus.objects.filter(
                business_id=bus.id,
                # path_id=path_id,
                business_role_allocation_id__in=role_alloc_ids
            ).exclude(come_status=9).update(come_status=1, sitting_status=1, stand_status=2)
            # 报告席
            report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()

            role_list = []
            for role_alloc_id in role_alloc_ids:
                bra = BusinessRoleAllocation.objects.get(pk=role_alloc_id)
                no = bra.no
                role = bra.role
                report_exists = BusinessReportStatus.objects.filter(business_id=bus.pk,
                                                                    business_role_allocation_id=role_alloc_id,
                                                                    path_id=path_id,
                                                                    schedule_status=const.SCHEDULE_UP_STATUS).exists()
                if report_exists:
                    BusinessReportStatus.objects.filter(business_id=bus.pk, business_role_allocation_id=role_alloc_id,
                                                        path_id=path_id, schedule_status=const.SCHEDULE_UP_STATUS) \
                        .update(schedule_status=const.SCHEDULE_INIT_STATUS)
                    pos = report_pos
                else:
                    role_position = FlowRolePosition.objects.filter(node_id=node.pk, role_id=role.flow_role_id,
                                                                    no=no).first()
                    pos = FlowPosition.objects.filter(pk=role_position.position_id).first()

                # 占位状态更新
                BusinessPositionStatus.objects.filter(business_id=bus.id, business_role_allocation__node_id=node.id,
                                                      path_id=path_id, position_id=pos.id).update(sitting_status=1,
                                                                                                  business_role_allocation_id=None)

                role_list.append({
                    'id': role_alloc_id, 'name': role.name,
                    'code_position': pos.code_position if pos else ''
                })
        return True, role_list
    except Exception as e:
        logger.exception(u'action_role_letout Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_letin(bus, node_id, path_id, role_alloc_ids):
    """
    请入
    :param exp: 实验
    :param node_id: 环节id
    :param role_ids: 角色id列表
    :return:
    """
    try:
        project = Project.objects.get(pk=bus.cur_project_id)
        role_list = []
        alloc_role_status_list = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            # path_id=path_id,
            business_role_allocation_id__in=role_alloc_ids
        )
        for alloc_role_status in alloc_role_status_list:
            item_role_id = alloc_role_status.business_role_allocation.role_id
            item_no = alloc_role_status.business_role_allocation.no
            business_role = BusinessRole.objects.filter(pk=item_role_id).first()

            if business_role:
                role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                role_id=business_role.flow_role_id, no=item_no).first()
                image = RoleImage.objects.filter(pk=FlowRoleAllocation.objects.get(
                    pk=alloc_role_status.business_role_allocation.flow_role_alloc_id).image_id).first()

            else:
                continue

            qs_files = RoleImageFile.objects.filter(image=image)
            actors = []
            if role_position:
                pos = FlowPosition.objects.filter(pk=role_position.position_id).first()
                if pos:
                    # 占位状态更新
                    pos_status = BusinessPositionStatus.objects.filter(business_id=bus.id,
                                                                       business_role_allocation_id=alloc_role_status.business_role_allocation_id,
                                                                       path_id=path_id, position_id=pos.id).first()
                    if pos_status:
                        if pos_status.sitting_status == const.SITTING_UP_STATUS and alloc_role_status.come_status != 9:
                            pos_status.sitting_status = const.SITTING_DOWN_STATUS
                            pos_status.save(update_fields=['sitting_status'])
                            alloc_role_status.come_status = 2
                            alloc_role_status.sitting_status = const.SITTING_DOWN_STATUS
                            alloc_role_status.save(update_fields=['come_status', 'sitting_status'])
                        else:
                            continue
                    else:
                        # 占位状态
                        BusinessPositionStatus.objects.update_or_create(business_id=bus.id,
                                                                        business_role_allocation_id=alloc_role_status.business_role_allocation_id,
                                                                        path_id=path_id, position_id=pos.id,
                                                                        defaults={'sitting_status': 2})
                        if alloc_role_status.come_status != 9:
                            alloc_role_status.come_status = 2
                            alloc_role_status.sitting_status = const.SITTING_DOWN_STATUS
                            alloc_role_status.save(update_fields=['come_status', 'sitting_status'])

                    if pos.actor1:
                        actor1 = qs_files.filter(direction=pos.actor1).first()
                        actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
                    if pos.actor2:
                        actor2 = qs_files.filter(direction=pos.actor2).first()
                        actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')
                    position = {'id': pos.id, 'position': pos.position, 'code_position': pos.code_position}
                else:
                    continue
            else:
                continue

            role_list.append({
                'role_id': alloc_role_status.business_role_allocation_id, 'role_name': business_role.name,
                'user': user_simple_info(BusinessTeamMember.objects.get(
                    business_id=bus.id,
                    business_role_id=alloc_role_status.business_role_allocation.role_id,
                    no=alloc_role_status.business_role_allocation.no,
                ).user_id),
                'come_status': alloc_role_status.come_status,
                'sitting_status': alloc_role_status.sitting_status,
                'stand_status': alloc_role_status.stand_status, 'position': position,
                'actors': actors, 'gender': image.gender if image else 1
            })
        return True, role_list
    except Exception as e:
        logger.exception(u'action_role_letin Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_sitdown(bus, path_id, role, pos, role_alloc_id):
    """
    坐下
    :return:
    """
    try:
        print role_alloc_id
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).update(stand_status=2)

        role_info = {'id': role_alloc_id, 'name': role.name, 'code_position': pos['code_position']}
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_sitdown Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_stand(bus, path_id, role, pos, role_alloc_id):
    """
    起立
    :return:
    """
    try:
        print role_alloc_id
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).update(stand_status=1)

        role_info = {'id': role_alloc_id, 'name': role.name, 'code_position': pos['code_position']}
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_stand Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_hide(bus, path_id, role, pos, role_alloc_id):
    """
    退席
    :return:
    """
    try:
        with transaction.atomic():
            BusinessRoleAllocationStatus.objects.filter(
                business_id=bus.id,
                business_role_allocation_id=role_alloc_id,
                # path_id=path_id
            ).update(stand_status=2, sitting_status=1)
            # 占位状态
            BusinessPositionStatus.objects.update_or_create(
                business_id=bus.id,
                business_role_allocation_id=role_alloc_id,
                path_id=path_id,
                position_id=pos['position_id'],
                defaults={'sitting_status': const.SITTING_UP_STATUS, 'business_role_allocation_id': None}
            )
            role_info = {'id': role_alloc_id, 'name': role.name, 'code_position': pos['code_position']}

        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_hide Exception:{}'.format(str(e)))
        return False, str(e)


def action_role_show(bus, node_id, path_id, role, pos, role_alloc_id):
    """
    入席
    :return:
    """
    try:
        # 角色状态
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).update(stand_status=2, sitting_status=2)

        alloc_role_status = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id,
        ).first()

        # 占位状态
        BusinessPositionStatus.objects.update_or_create(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            path_id=path_id,
            position_id=pos['position_id'],
            defaults={'sitting_status': const.SITTING_DOWN_STATUS}
        )

        image = RoleImage.objects.filter(pk=FlowRoleAllocation.objects.get(
            pk=BusinessRoleAllocation.objects.get(pk=role_alloc_id).flow_role_alloc_id).image_id).first()
        qs_files = RoleImageFile.objects.filter(image=image)
        actors = []
        if pos['actor1']:
            actor1 = qs_files.filter(direction=pos['actor1']).first()
            actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
        if pos['actor2']:
            actor2 = qs_files.filter(direction=pos['actor2']).first()
            actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')
        position = {'id': pos['position_id'], 'position': pos['position'], 'code_position': pos['code_position']}

        role_info = {
            'role_id': alloc_role_status.business_role_allocation_id,
            'user': user_simple_info(BusinessTeamMember.objects.get(
                business_id=bus.id,
                business_role_id=alloc_role_status.business_role_allocation.role_id,
                no=alloc_role_status.business_role_allocation.no,
            ).user_id),
            'come_status': alloc_role_status.come_status, 'sitting_status': alloc_role_status.sitting_status,
            'stand_status': alloc_role_status.stand_status, 'position': position,
            'actors': actors, 'gender': image.gender if image else 1
        }
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_show Exception:{}'.format(str(e)))
        return False, str(e)


def action_doc_apply_submit_opt(bus, node_id, path_id, data):
    """
    申请提交操作结果
    :param exp: 实验
    :param node_id: 环节id
    :param role_id: 角色id
    :param is_pass: 是否同意: 1,同意；2，不同意
    :return:
    """
    try:
        if 'msg_id' in data.keys():
            BusinessMessage.objects.filter(pk=data['msg_id']).update(opt_status=True)
        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            # path_id=path_id,
            business_role_allocation_id=data['role_alloc_id']
        ).update(submit_status=data['result'])
        role = BusinessRoleAllocation.objects.get(pk=data['role_alloc_id']).role
        return True, {'role_id': data['role_alloc_id'], 'role_name': role.name, 'result': data['result']}
    except Exception as e:
        logger.exception(u'action_doc_apply_submit_opt Exception:{}'.format(str(e)))
        return False, str(e)


def action_doc_submit(doc_ids):
    """
    提交
    :return:
    """
    try:
        doc_list = []
        for doc_id in doc_ids:
            doc = BusinessDoc.objects.filter(pk=doc_id).first()
            doc_list.append({
                'id': doc.id, 'name': doc.filename, 'url': doc.file.url, 'file_type': doc.file_type
            })
        return True, doc_list
    except Exception as e:
        logger.exception(u'action_role_apply_submit Exception:{}'.format(str(e)))
        return False, str(e)


# def action_exp_restart(exp, user_id):
#     """
#     重新开始实验
#     :param exp: 实验
#     :return:
#     """
#     try:
#         if exp and exp.status == 2:
#             # 查询小组组长
#             team = Team.objects.filter(pk=exp.team_id).first()
#             can_opt = True if exp.created_by == user_id or team.leader == user_id else False
#             if can_opt is False:
#                 resp = code.get_msg(code.EXPERIMENT_PERMISSION_DENIED)
#                 return False, resp
#             # 初始项目
#             project = Project.objects.get(pk=exp.project_id)
#             first_node_id = get_start_node(project.flow_id)
#             logger.info('first_node_id: {}'.format(first_node_id))
#
#             with transaction.atomic():
#                 # 删除实验流程中产生的相关信息（文件、心得、消息、笔记、编辑内容）
#                 ExperimentDoc.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentExperience.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentMessage.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentMessageFile.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentNotes.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentDocContent.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentRoleStatus.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentReportStatus.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentPositionStatus.objects.filter(experiment_id=exp.id).delete()
#                 ExperimentTransPath.objects.filter(experiment_id=exp.id).delete()
#
#                 # 清除跳转项目用户角色配置
#                 MemberRole.objects.filter(experiment_id=exp.id).exclude(project_id=exp.project_id).delete()
#
#                 # 实验路径
#                 node = FlowNode.objects.get(pk=first_node_id)
#                 path = ExperimentTransPath.objects.create(experiment_id=exp.pk, node_id=first_node_id,
#                                                           project_id=exp.project_id, task_id=node.task_id, step=1)
#
#                 # 设置初始环节角色状态信息
#                 allocation = ProjectRoleAllocation.objects.filter(project_id=project.pk, node_id=first_node_id)
#                 role_status_list = []
#                 for item in allocation:
#                     if item.can_brought:
#                         come_status = 1
#                     else:
#                         come_status = 9
#                     # role_status_list.append(ExperimentRoleStatus(experiment_id=exp.id, node_id=item.node_id,
#                     #                                              path_id=path.pk, role_id=item.role_id,
#                     #                                              come_status=come_status))
#                     # 三期 - 不能直接创建， 在service中结束并走向下一环节的时候会创建角色状态，这里再创建一次就重复了
#                     ers = ExperimentRoleStatus.objects.filter(experiment_id=exp.id, node_id=item.node_id,
#                                                               path_id=path.pk,
#                                                               role_id=item.role_id)
#                     if ers:  # 存在则更新
#                         ers = ers.first()
#                         ers.come_status = come_status
#                         ers.save()
#                     else:  # 不存在则创建
#                         ExperimentRoleStatus.objects.update_or_create(experiment_id=exp.id, node_id=item.node_id,
#                                                                       path_id=path.pk, role_id=item.role_id,
#                                                                       come_status=come_status)
#
#                 # ExperimentRoleStatus.objects.bulk_create(role_status_list)
#                 # 设置环节中用户的角色状态
#                 member_roles = MemberRole.objects.filter(experiment_id=exp.id, del_flag=0)
#                 for item in member_roles:
#                     ExperimentRoleStatus.objects.filter(experiment_id=exp.id,
#                                                         role_id=item.role_id).update(user_id=item.user_id)
#                 exp.cur_project_id = exp.project_id
#                 exp.node_id = first_node_id
#                 exp.path_id = path.pk
#                 exp.save()
#             node = FlowNode.objects.filter(pk=first_node_id).first()
#             opt = {
#                 'node_id': node.id, 'name': node.name, 'condition': node.condition,
#                 'experiment_id': exp.pk, 'process_type': node.process.type
#             }
#             return True, opt
#         elif exp is None:
#             resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
#             return False, resp
#         elif exp.status == 9:
#             resp = code.get_msg(code.EXPERIMENT_HAS_FINISHED)
#             return False, resp
#         elif exp.status == 1:
#             resp = code.get_msg(code.EXPERIMENT_HAS_NOT_STARTED)
#             return False, resp
#         else:
#             # resp = code.get_msg(code.SYSTEM_ERROR)
#             # return False, resp
#             pass
#     except Exception as e:
#         logger.exception(u'action_exp_restart Exception:{}'.format(str(e)))
#         resp = code.get_msg(code.SYSTEM_ERROR)
#         return False, resp


# def action_exp_back(bus):
#     """
#     实验环节回退
#     :param exp: 实验
#     :return:
#     """
#     try:
#         if bus.status == 9:  # 如果实验已结束
#             resp = code.get_msg(code.EXPERIMENT_HAS_FINISHED)
#             return False, resp
#         elif bus.status == 1:  # 如果实验还未开始
#             resp = code.get_msg(code.EXPERIMENT_HAS_NOT_STARTED)
#             return False, resp
#         else:  # 如果实验正在进行中
#             previous_path = get_pre_node_path(bus)
#             if previous_path:
#                 previous_node = FlowNode.objects.filter(pk=previous_path.node_id).first()
#                 if previous_node is None:
#                     resp = code.get_msg(code.EXPERIMENT_IN_FIRST_NODE)
#                     return False, resp
#
#                 cur_node_id = bus.node_id
#                 with transaction.atomic():
#                     # 删除当前环节路径已保存的信息
#                     cur_path = BusinessTransPath.objects.filter(business_id=bus.id).last()
#                     BusinessDoc.objects.filter(business_id=bus.id, node_id=cur_node_id, path_id=cur_path.id).delete()
#                     BusinessExperience.objects.filter(business_id=bus.id).delete()
#                     BusinessMessage.objects.filter(business_id=bus.id, business_role_allocation__node_id=cur_node_id, path_id=cur_path.id).delete()
#                     BusinessMessageFile.objects.filter(business_id=bus.id, node_id=cur_node_id, path_id=cur_path.id).delete()
#                     BusinessNotes.objects.filter(business_id=bus.id, node_id=cur_node_id).delete()
#                     BusinessDocContent.objects.filter(business_id=bus.id, node_id=cur_node_id).delete()
#                     BusinessRoleAllocationStatus.objects.filter(business_id=bus.id, path_id=cur_path.pk).delete()
#                     BusinessReportStatus.objects.filter(business_id=bus.id, path_id=cur_path.pk).delete()
#                     BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=cur_path.pk).delete()
#
#                     # 如上一环节和当前环节项目不一致，清除跳转项目用户角色配置
#                     if cur_path.project_id != previous_path.project_id:
#                         MemberRole.objects.filter(business_id=bus.id, project_id=cur_path.project_id).delete()
#
#                     # 删除最后一步
#                     if cur_path.step > 1:
#                         cur_path.delete()
#                     else:
#                         first_count = BusinessTransPath.objects.filter(business_id=bus.id, step=1).count()
#                         if first_count > 1:
#                             BusinessTransPath.objects.filter(business_id=bus.id, step=1).last().delete()
#
#                     path = BusinessTransPath.objects.filter(business_id=bus.id).last()
#
#                     bus.cur_project_id = previous_path.project_id
#                     bus.node_id = previous_path.node_id
#                     bus.path_id = path.pk
#                     bus.save()
#                     opt = {
#                         'node_id': previous_node.id, 'name': previous_node.name, 'condition': previous_node.condition,
#                         'business_id': bus.id, 'process_type': previous_node.process.type
#                     }
#                     return True, opt
#             else:
#                 resp = code.get_msg(code.EXPERIMENT_IN_FIRST_NODE)
#                 return False, resp
#     except Exception as e:
#         logger.exception(u'action_exp_back Exception:{}'.format(str(e)))
#         resp = code.get_msg(code.SYSTEM_ERROR)
#         return False, resp


def action_exp_node_end(bus, role_alloc_id, data):
    """
    结束实验环节
    :param tran_id: 环节流转id
    :param exp: 实验
    :param role_id: 实验角色id
    :return:
    """
    try:
        is_nest = False
        # 当前项目环节权限判断
        if not BusinessRoleAllocation.objects.filter(pk=role_alloc_id, project_id=bus.cur_project_id,
                                                     can_terminate=True).exists():
            resp = code.get_msg(code.PERMISSION_DENIED)
            return False, resp
        else:
            cur_node = FlowNode.objects.filter(pk=data['cur_node']).first()
            if data['parallel'] == 0 or data['parallel'] == '0' or (cur_node.is_parallel_merging == 1 and bus.parallel_count == 1):
                if cur_node.is_parallel_merging == 1:
                    bus.parallel_passed_nodes.create(
                        node=cur_node
                    )
                if data['tran_id'] == 0 or data['tran_id'] == '0':
                    next_node = None
                elif data['process_type'] == const.PROCESS_EXPERIENCE_TYPE:
                    bpt = BusinessProjectTrack.objects.filter(business_id=bus.id,
                                                              process_type=const.PROCESS_NEST_TYPE).last()
                    if bpt is None or bpt.project_id == bus.cur_project_id:
                        tran = FlowTrans.objects.get(pk=data['tran_id'])
                        next_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.outgoing).first()
                    else:
                        bus.jumper_id = None
                        data['project_id'] = bpt.project_id
                        tran = FlowTrans.objects.get(pk=bpt.flow_trans_id)
                        next_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.outgoing).first()
                        is_nest = True
                else:
                    tran = FlowTrans.objects.get(pk=data['tran_id'])
                    next_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.outgoing).first()

                if 'project_id' in data.keys() and data['project_id']:
                    # 如果是跳转项目
                    project = Project.objects.filter(pk=data['project_id']).first()
                else:
                    project = Project.objects.filter(pk=bus.cur_project_id).first()

                if next_node is None:
                    # 结束实验，验证实验心得
                    experience_count = BusinessExperience.objects.filter(business_id=bus.id, del_flag=0).count()
                    bras = BusinessRoleAllocation.objects.filter(project_id=project.pk, node_id=bus.node_id,
                                                                 can_take_in=True)
                    user_ids = []
                    for bra in bras:
                        btm = BusinessTeamMember.objects.filter(business_id=bus.id, project_id=project.pk, del_flag=0,
                                                                business_role_id=bra.role_id, no=bra.no).first()
                        if btm and btm.user_id:
                            user_ids.append(btm.user_id)
                    # logger.info(role_ids)
                    print user_ids
                    user_count = len(user_ids)
                    logger.info('user_count=%s' % user_count)
                    if experience_count < user_count:
                        resp = code.get_msg(code.EXPERIMENT_EXPERIENCE_USER_NOT_SUBMIT)
                        return False, resp

                    bus.status = 9
                    bus.finish_time = datetime.now()
                    process_type = 0
                else:
                    process_type = next_node.process.type
                    cur_node = FlowNode.objects.filter(pk=bus.node_id).first()
                    # 判断是否投票环节和配置
                    cur_path = BusinessTransPath.objects.filter(business_id=bus.pk).last()

                    # 创建新环节路径
                    step = BusinessTransPath.objects.filter(business_id=bus.id).count() + 1
                    path = BusinessTransPath.objects.create(business_id=bus.id, node_id=next_node.pk, project_id=project.pk,
                                                            task_id=next_node.task_id, step=step)
                    # 设置初始环节角色状态信息 按实验路径创建
                    role_allocations = BusinessRoleAllocation.objects.filter(project_id=project.pk, node_id=next_node.pk)

                    role_status_list = []
                    for role_allocation_item in role_allocations:
                        if role_allocation_item.can_brought:
                            come_status = 1
                        else:
                            come_status = 9
                        # role_status_list.append(
                        #     ExperimentRoleStatus(experiment_id=exp.id, node_id=item.node_id, path_id=path.pk,
                        #                          role_id=item.role_id, come_status=come_status))
                        # 三期 - 不能直接创建， 在service中结束并走向下一环节的时候会创建角色状态，这里再创建一次就重复了
                        bras = BusinessRoleAllocationStatus.objects.filter(
                            business_id=bus.id,
                            business_role_allocation_id=role_allocation_item.id,
                            # path_id=path.pk,
                        )
                        if bras:  # 存在则更新
                            bras = bras.first()
                            bras.come_status = come_status
                            bras.save()
                        else:  # 不存在则创建
                            BusinessRoleAllocationStatus.objects.update_or_create(
                                business_id=bus.id,
                                # path_id=path.pk,
                                business_role_allocation_id=role_allocation_item.id,
                                come_status=come_status
                            )
                    # ExperimentRoleStatus.objects.bulk_create(role_status_list)

                    # 设置环节中用户的角色状态
                    business_team_members = BusinessTeamMember.objects.filter(business_id=bus.id, project_id=project.pk,
                                                                              del_flag=0)
                    for item in business_team_members:
                        # BusinessRoleAllocationStatus.objects.filter(
                        #     business_id=bus.id,
                        #     business_role_allocation=BusinessRoleAllocation.objects.get(role_id=item.business_role_id, no=item.no),
                        # ).update(user_id=item.user_id)
                        # 三期 - 当上下两个环节的场景一样、角色一致，则下一个环节启动后，所有具备入席权限的角色自动在席
                        # 这样实现不行，会引入重复角色的bug
                        if cur_node.process_id == next_node.process_id and not is_nest:
                            item_role = item.business_role
                            # 角色占位
                            pos = get_role_position(bus, project, next_node, item_role, role_alloc_id)
                            if pos:
                                # 占位状态, 如果上一环节占位存在并且已入席则创建当前环节占位数据
                                bps = BusinessPositionStatus.objects.filter(
                                    business_id=bus.id,
                                    path_id=cur_path.id,
                                    business_role_allocation__node_id=cur_node.id,
                                    business_role_allocation__no=item.no,
                                    business_role_allocation__role_id=item.business_role_id
                                ).first()
                                if bps and bps.sitting_status == const.SITTING_DOWN_STATUS:
                                    BusinessPositionStatus.objects.filter(
                                        business_id=bus.id,
                                        path_id=path.id,
                                        business_role_allocation__node_id=next_node.pk,
                                        business_role_allocation__no=item.no,
                                        business_role_allocation__role_id=item.business_role_id
                                    ).update(sitting_status=const.SITTING_DOWN_STATUS)
                                # 角色状态， 如果上一环节角色存在并且已入席则创建当前环节占位数据
                                bras = BusinessRoleAllocationStatus.objects.filter(
                                    business_id=bus.id,
                                    business_role_allocation__node_id=cur_node.id,
                                    business_role_allocation__no=item.no,
                                    business_role_allocation__role_id=item.business_role_id,
                                    # path_id=cur_path.id
                                ).first()
                                if bras and bras.sitting_status == const.SITTING_DOWN_STATUS:
                                    BusinessRoleAllocationStatus.objects.filter(
                                        business_id=bus.id,
                                        business_role_allocation__node_id=next_node.pk,
                                        business_role_allocation__no=item.no,
                                        business_role_allocation__role_id=item.business_role_id,
                                        # path_id=path.id
                                    ).update(sitting_status=const.SITTING_DOWN_STATUS)

                    bus.cur_project_id = project.pk
                    bus.node_id = next_node.pk
                    bus.path_id = path.pk
                bus.save()

                opt = {'node_id': next_node.pk if next_node else None, 'status': bus.status,
                       'business_id': bus.pk, 'process_type': process_type}
                return True, opt
            elif data['parallel'] == 1 or data['parallel'] == '1':
                if cur_node.is_parallel_merging == 1:
                    cur_count = bus.parallel_count
                    bus.parallel_count = cur_count - 1
                    bus.save()
                if data['select'] == 2 or data['select'] == 3:
                    tran = FlowTrans.objects.get(pk=data['trans'][0]['id'])
                    parallel_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.incoming).first()
                elif FlowTrans.objects.filter(incoming=cur_node.task_id).count() > 1:
                    tran = FlowTrans.objects.get(pk=data['tran_id'])
                    parallel_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.outgoing).first()
                else:
                    parallel_node = FlowNode.objects.get(flow_id=cur_node.flow_id, task_id=FlowTrans.objects.get(incoming=cur_node.task_id).outgoing)
                project = Project.objects.filter(pk=bus.cur_project_id).first()
                if parallel_node.parallel_node_start == 1:
                    for item in data['trans']:
                        tran = FlowTrans.objects.get(pk=item['id'])
                        next_node = FlowNode.objects.filter(flow_id=tran.flow_id, task_id=tran.outgoing).first()
                        role_allocations = BusinessRoleAllocation.objects.filter(project_id=project.pk, node_id=next_node.pk)

                        for role_allocation_item in role_allocations:
                            if role_allocation_item.can_brought:
                                come_status = 1
                            else:
                                come_status = 9

                            bras = BusinessRoleAllocationStatus.objects.filter(
                                business_id=bus.id,
                                business_role_allocation_id=role_allocation_item.id,
                            )
                            if bras:
                                bras = bras.first()
                                bras.come_status = come_status
                                bras.save()
                            else:
                                BusinessRoleAllocationStatus.objects.update_or_create(
                                    business_id=bus.id,
                                    business_role_allocation_id=role_allocation_item.id,
                                    come_status=come_status
                                )

                        business_team_members = BusinessTeamMember.objects.filter(business_id=bus.id, project_id=project.pk, del_flag=0)
                        for bitem in business_team_members:

                            if cur_node.process_id == next_node.process_id and not is_nest:
                                item_role = bitem.business_role

                                pos = get_role_position(bus, project, next_node, item_role, role_alloc_id)
                                if pos:

                                    bps = BusinessPositionStatus.objects.filter(
                                        business_id=bus.id,
                                        business_role_allocation__node_id=cur_node.id,
                                        business_role_allocation__no=bitem.no,
                                        business_role_allocation__role_id=bitem.business_role_id
                                    ).first()
                                    if bps and bps.sitting_status == const.SITTING_DOWN_STATUS:
                                        BusinessPositionStatus.objects.filter(
                                            business_id=bus.id,
                                            business_role_allocation__node_id=next_node.pk,
                                            business_role_allocation__no=bitem.no,
                                            business_role_allocation__role_id=bitem.business_role_id
                                        ).update(sitting_status=const.SITTING_DOWN_STATUS)

                                    bras = BusinessRoleAllocationStatus.objects.filter(
                                        business_id=bus.id,
                                        business_role_allocation__node_id=cur_node.id,
                                        business_role_allocation__no=bitem.no,
                                        business_role_allocation__role_id=bitem.business_role_id,
                                    ).first()
                                    if bras and bras.sitting_status == const.SITTING_DOWN_STATUS:
                                        BusinessRoleAllocationStatus.objects.filter(
                                            business_id=bus.id,
                                            business_role_allocation__node_id=next_node.pk,
                                            business_role_allocation__no=bitem.no,
                                            business_role_allocation__role_id=bitem.business_role_id,
                                        ).update(sitting_status=const.SITTING_DOWN_STATUS)
                        bus.parallel_nodes.create(node=next_node)
                    bus.cur_project_id = project.pk
                    bus.parallel_passed_nodes.create(
                        node=cur_node
                    )
                    cur_count = bus.parallel_count
                    bus.parallel_count = cur_count + 1
                    bus.parallel_passed_nodes.create(
                        node=parallel_node
                    )
                    if data['select'] == 2 or data['select'] == 3:
                        bus.node_id = parallel_node.pk
                        step_now = BusinessTransPath.objects.filter(business_id=bus.id).count() + 1
                        path_now = BusinessTransPath.objects.create(business_id=bus.id, node_id=parallel_node.pk, project_id=project.pk,
                                                                    task_id=parallel_node.task_id, step=step_now)
                        bus.path_id = path_now.pk
                    bus.parallel_nodes.filter(node=cur_node).delete()
                    bus.save()
                    return True, {}
                else:
                    next_node = parallel_node
                    project = Project.objects.filter(pk=bus.cur_project_id).first()
                    role_allocations = BusinessRoleAllocation.objects.filter(project_id=project.pk, node_id=next_node.pk)

                    for role_allocation_item in role_allocations:
                        if role_allocation_item.can_brought:
                            come_status = 1
                        else:
                            come_status = 9

                        bras = BusinessRoleAllocationStatus.objects.filter(
                            business_id=bus.id,
                            business_role_allocation_id=role_allocation_item.id,
                        )
                        if bras:
                            bras = bras.first()
                            bras.come_status = come_status
                            bras.save()
                        else:
                            BusinessRoleAllocationStatus.objects.update_or_create(
                                business_id=bus.id,
                                business_role_allocation_id=role_allocation_item.id,
                                come_status=come_status
                            )

                    business_team_members = BusinessTeamMember.objects.filter(business_id=bus.id, project_id=project.pk, del_flag=0)
                    for bitem in business_team_members:

                        if cur_node.process_id == next_node.process_id and not is_nest:
                            item_role = bitem.business_role

                            pos = get_role_position(bus, project, next_node, item_role, role_alloc_id)
                            if pos:

                                bps = BusinessPositionStatus.objects.filter(
                                    business_id=bus.id,
                                    business_role_allocation__node_id=cur_node.id,
                                    business_role_allocation__no=bitem.no,
                                    business_role_allocation__role_id=bitem.business_role_id
                                ).first()
                                if bps and bps.sitting_status == const.SITTING_DOWN_STATUS:
                                    BusinessPositionStatus.objects.filter(
                                        business_id=bus.id,
                                        business_role_allocation__node_id=next_node.pk,
                                        business_role_allocation__no=bitem.no,
                                        business_role_allocation__role_id=bitem.business_role_id
                                    ).update(sitting_status=const.SITTING_DOWN_STATUS)

                                bras = BusinessRoleAllocationStatus.objects.filter(
                                    business_id=bus.id,
                                    business_role_allocation__node_id=cur_node.id,
                                    business_role_allocation__no=bitem.no,
                                    business_role_allocation__role_id=bitem.business_role_id,
                                ).first()
                                if bras and bras.sitting_status == const.SITTING_DOWN_STATUS:
                                    BusinessRoleAllocationStatus.objects.filter(
                                        business_id=bus.id,
                                        business_role_allocation__node_id=next_node.pk,
                                        business_role_allocation__no=bitem.no,
                                        business_role_allocation__role_id=bitem.business_role_id,
                                    ).update(sitting_status=const.SITTING_DOWN_STATUS)
                    bus.cur_project_id = project.pk
                    bus.parallel_passed_nodes.create(
                        node=cur_node
                    )
                    if bus.parallel_nodes.filter(node=next_node).count() == 0:
                        bus.parallel_nodes.create(node=next_node)
                    bus.parallel_nodes.filter(node=cur_node).delete()
                    bus.save()
                    return True, {}
    except Exception as e:
        logger.exception(u'action_exp_node_end Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_exp_finish(bus, user_id):
    """
    提前结束实验
    :param exp: 实验
    :param user_id: 用户
    :return:
    """
    try:
        if bus.status == const.EXPERIMENT_WAITING:
            resp = code.get_msg(code.EXPERIMENT_HAS_NOT_STARTED)
            result = False
        elif bus.status == const.EXPERIMENT_PROCESSING:
            bus.status = const.EXPERIMENT_FINISHED
            bus.finish_time = datetime.now()
            bus.save()
            opt = {'status': bus.status,
                   'business_id': bus.pk}
            result, resp = True, opt
        else:
            resp = code.get_msg(code.EXPERIMENT_HAS_FINISHED)
            result = False
        return result, resp
    except Exception as e:
        logger.exception(u'action_exp_finish Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_submit_experience(bus, content, user_id):
    """
    实验
    :param exp: 实验
    :param content: 心得内容
    :param user_id 用户id
    :return:
    """
    try:
        if bus.status == 2:
            if content is None or len(content) > 30000:
                return False, code.get_msg(code.PARAMETER_ERROR)

            if BusinessExperience.objects.filter(business_id=bus.id, created_by=user_id, status=2).exists():
                return False, code.get_msg(code.BUSINESS_EXPERIENCE_HAS_EXIST)

            instance, flag = BusinessExperience.objects.update_or_create(business_id=bus.id, created_by_id=user_id,
                                                                         defaults={'content': content,
                                                                                   'created_by_id': user_id,
                                                                                   'status': 2})
            opt = {
                'id': instance.id, 'content': instance.content, 'status': instance.status,
                'created_by': user_simple_info(instance.created_by_id),
                'create_time': instance.create_time.strftime('%Y-%m-%d')
            }
            return True, opt
        elif bus.status == 1:
            return False, code.get_msg(code.EXPERIMENT_HAS_NOT_STARTED)
        else:
            return False, code.get_msg(code.EXPERIMENT_HAS_FINISHED)
    except Exception as e:
        logger.exception(u'action_submit_experience Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_vote(bus, node_id, path, role_alloc_id, status):
    """
    实验投票
    :param exp: 实验
    :param node_id: 环节id
    :param path_id 路径id
    :param role_id 角色id
    :param status 投票状态
    :return:
    """
    try:
        if path.vote_status == 2:
            return False, code.get_msg(code.BUSINESS_ROLE_VOTE_IS_END)

        exists = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            # path_id=path.pk,
            vote_status=0).exists()
        if not exists:
            return False, code.get_msg(code.BUSINESS_ROLE_HAS_VOTE)

        BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            # path_id=path.pk
        ).update(vote_status=status)

        has_vote = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            # path_id=path.pk,
            vote_status=0).exists()
        opt = {
            'role_status_list': action_roles_vote_status(bus, node_id, path),
            'has_vote': False if has_vote else True,
            'end_vote': False
        }
        return True, opt

    except Exception as e:
        logger.exception(u'action_role_vote Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_vote_end(bus, node_id, path):
    """
    实验投票
    :param exp: 实验
    :param node_id: 环节id
    :param path_id 路径id
    :return:
    """
    try:
        path.vote_status = 2
        path.save()
        opt = {
            'role_status_list': action_roles_vote_status(bus, node_id, path), 'end_vote': True
        }
        return True, opt

    except Exception as e:
        logger.exception(u'action_role_vote_end Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_request_sign(bus, node_id, data):
    """
    要求签字
    :param exp: 实验
    :param data
    :return:
    """
    try:
        obj = BusinessDocSign.objects.filter(business_id=bus.pk, business_role_allocation_id=data['role_alloc_id'],
                                             doc_id=data['doc_id']).first()
        if obj:
            return False, code.get_msg(code.BUSINESS_HAS_REQUEST_SIGN_ERROR)
        else:
            BusinessDocSign.objects.create(business_id=bus.pk, business_role_allocation_id=data['role_alloc_id'],
                                           doc_id=data['doc_id'])

        doc = BusinessDoc.objects.filter(id=data['doc_id']).first()
        opt = {"doc_id": doc.pk, "doc_name": doc.filename, 'url': doc.file.url, 'file_type': doc.file_type,
               "role_alloc_id": data['role_alloc_id'], "role_name": data['role_name']}
        return True, opt
    except Exception as e:
        logger.exception(u'action_role_request_sign Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_sign(bus, sign, node_id, role_alloc_id, data):
    """
    签字msg_id, doc_id, doc_name,
    :param exp: 实验
    :param data
    :return:
    """
    try:
        if 'msg_id' in data.keys():
            BusinessMessage.objects.filter(pk=data['msg_id']).update(opt_status=True)

        BusinessDocSign.objects.filter(business_id=bus.pk, business_role_allocation_id=role_alloc_id,
                                       doc_id=data['doc_id']).update(sign=sign, sign_status=data['result'])
        opt = {
            'doc_id': data['doc_id'], 'doc_name': data['doc_name'], 'name': sign, 'result': data['result']
        }
        return True, opt
    except Exception as e:
        logger.exception(u'action_role_sign Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_schedule_report(bus, node_id, path_id, data):
    """
    安排报告
    :param exp: 实验
    :param node_id: 环节id
    :param path_id 路径id
    :param role_id 角色id
    :return:
    """
    try:
        # 判断是否有报告席
        node = FlowNode.objects.filter(pk=bus.node_id, del_flag=0).first()
        position = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()
        if position is None:
            return False, code.get_msg(code.EXPERIMENT_ROLE_REPORT_ERROR)

        # 占位状态
        BusinessPositionStatus.objects.update_or_create(business_id=bus.pk, path_id=path_id, position_id=position.pk)
        # 报告状态
        BusinessReportStatus.objects.update_or_create(
            business_id=bus.pk,
            path_id=path_id,
            business_role_allocation_id=data['role_alloc_id'],
            position_id=position.pk,
            defaults={'schedule_status': const.SCHEDULE_OK_STATUS}
        )
        opt = {
            'role_alloc_id': data['role_alloc_id'], 'role_name': data['role_name'],
            'schedule_status': const.SCHEDULE_OK_STATUS,
            'up_btn_status': const.FALSE, 'down_btn_status': const.FALSE
        }
        return True, opt

    except Exception as e:
        logger.exception(u'action_role_schedule_report Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_toward_report(bus, node_id, path_id, bra, pos):
    """
    走向发言席：
    1、判断场景报告席是否配置正确；
    2、判断报告席占位是否占用；
    3、判断是否安排了发言；
    4、角色如以入席，修改占位和入席状态，修改报告席状态，未入席直接修改报告席状态；
    5、结果消息：动画cmd，报告席状态，报告按钮状态；
    :param exp: 实验
    :param node_id: 环节id
    :param path_id 路径id
    :param role_id 角色id
    :return:
    """
    try:
        logger.info('exp.id:%s,node_id:%s,path_id:%s,role_id:%s,position_id:%s' % (bus.pk, node_id, path_id, bra.id,
                                                                                   pos['position_id']))
        # 1判断是否有报告席
        btm = BusinessTeamMember.objects.filter(business_id=bus.id, business_role_id=bra.role_id,
                                                no=bra.no).first()
        node = FlowNode.objects.filter(pk=bus.node_id, del_flag=0).first()
        report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()
        if report_pos is None:
            return False, code.get_msg(code.BUSINESS_ROLE_REPORT_ERROR)
        report_position = {'id': report_pos.id, 'position': report_pos.position,
                           'code_position': report_pos.code_position}

        origin_position = {'id': pos['position_id'], 'position': pos['position'],
                           'code_position': pos['code_position']}
        role_alloc_id = bra.id
        # 2判断报告席占位是否占用
        report_position_status = BusinessPositionStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            path_id=path_id,
            position_id=report_pos.pk
        ).first()
        if report_position_status is None:
            return False, code.get_msg(code.BUSINESS_ROLE_REPORT_ERROR)

        if report_position_status.sitting_status == const.SITTING_DOWN_STATUS:
            return False, code.get_msg(code.BUSINESS_POSITION_HAS_USE)

        # 3判断是否安排了发言；
        report_status = BusinessReportStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            path_id=path_id
        ).first()
        if report_status is None or report_status.schedule_status == const.SCHEDULE_INIT_STATUS:
            return False, code.get_msg(code.BUSINESS_ROLE_REPORT_SCHEDULE_ERROR)
        if report_status.schedule_status == const.SCHEDULE_UP_STATUS:
            return False, code.get_msg(code.BUSINESS_ROLE_HAS_IN_POSITION)

        # 修改状态为已上位
        report_status.schedule_status = const.SCHEDULE_UP_STATUS
        report_status.save()

        # 4角色如以入席，修改占位和入席状态，修改报告席状态，未入席直接修改报告席状态；
        # 角色状态
        brast = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.pk,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).first()

        BusinessPositionStatus.objects.update_or_create(business_id=bus.id, business_role_allocation_id=role_alloc_id,
                                                        path_id=path_id, position_id=pos['position_id'])
        # 原席位判断，如果当前角色入席原席位，如果其他角色入席原席位
        origin_position_status = BusinessPositionStatus.objects.filter(business_id=bus.pk,
                                                                       business_role_allocation_id=role_alloc_id,
                                                                       path_id=path_id,
                                                                       position_id=pos['position_id']).first()

        origin_position['sitting_status'] = origin_position_status.sitting_status
        origin_position['is_self'] = False
        if origin_position_status.business_role_allocation_id == role_alloc_id:
            origin_position['is_self'] = True

        if brast.sitting_status == const.SITTING_DOWN_STATUS:
            # 已入席修改原席位占位状态，退席
            BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=path_id,
                                                  position_id=pos['position_id']).update(
                sitting_status=const.SITTING_UP_STATUS,
                business_role_allocation_id=None)

        brast.stand_status = 2
        brast.sitting_status = 2
        brast.come_status = 2
        brast.save()

        # 报告席状态为已入席
        BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=path_id,
                                              position_id=report_pos.id).update(
            sitting_status=const.SITTING_DOWN_STATUS,
            business_role_allocation_id=role_alloc_id)

        image = RoleImage.objects.filter(pk=FlowRoleAllocation.objects.get(pk=bra.flow_role_alloc_id).image_id).first()
        qs_files = RoleImageFile.objects.filter(image=image)
        actors = []
        if report_pos.actor1:
            actor1 = qs_files.filter(direction=report_pos.actor1).first()
            actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
        if report_pos.actor2:
            actor2 = qs_files.filter(direction=report_pos.actor2).first()
            actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')

        role_info = {
            'role_alloc_id': bra.role_id, 'user': user_simple_info(btm.user_id),
            'come_status': brast.come_status, 'sitting_status': brast.sitting_status,
            'stand_status': brast.stand_status,
            'origin_position': origin_position, 'report_position': report_position,
            'up_btn_status': const.FALSE, 'down_btn_status': const.TRUE,
            'actors': actors, 'animate_cmd': u'cmd=trans&transname=走向发言席',
            'gender': image.gender if image else 1
        }
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_toward_report Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_role_end_report(bus, node_id, path_id, bra, pos):
    """
    走下发言席
    :param bus: 实验
    :param node_id: 环节id
    :param path_id 路径id
    :param role_id 角色id
    :return:
    """
    try:
        btm = BusinessTeamMember.objects.filter(business_id=bus.id, business_role_id=bra.role_id,
                                                no=bra.no).first()
        role_alloc_id = bra.id
        # 原占位
        origin_pos = FlowPosition.objects.filter(pk=pos['org_position_id']).first()
        origin_position = {'id': origin_pos.id, 'position': origin_pos.position,
                           'code_position': origin_pos.code_position}
        report_position = {'id': pos['position_id'], 'position': pos['position'],
                           'code_position': pos['code_position']}

        # 2判断是否安排了发言；
        report_status = BusinessReportStatus.objects.filter(business_id=bus.pk,
                                                            business_role_allocation_id=role_alloc_id,
                                                            path_id=path_id).first()
        if report_status is None or report_status.schedule_status != const.SCHEDULE_UP_STATUS:
            return False, code.get_msg(code.EXPERIMENT_ROLE_REPORT_SCHEDULE_ERROR)
        report_status.schedule_status = const.SCHEDULE_INIT_STATUS
        report_status.save()

        # 3角色如以入席，修改占位和入席状态，修改报告席状态，未入席直接修改报告席状态；
        # 修改原席位占位状态，入席, 判断原席位是否被其他角色占用
        origin_position_use = BusinessPositionStatus.objects.filter(business_id=bus.pk,
                                                                    business_role_allocation_id=role_alloc_id,
                                                                    path_id=path_id, position_id=origin_pos.id,
                                                                    sitting_status=const.SITTING_DOWN_STATUS).exists()
        if origin_position_use:
            BusinessRoleAllocationStatus.objects.filter(
                business_id=bus.id,
                business_role_allocation_id=role_alloc_id,
                # path_id=path_id
            ).update(stand_status=2, sitting_status=1, come_status=2)
        else:
            BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=path_id,
                                                  position_id=origin_pos.id,
                                                  business_role_allocation_id=role_alloc_id).update(
                sitting_status=const.SITTING_DOWN_STATUS)
            BusinessRoleAllocationStatus.objects.filter(
                business_id=bus.id,
                business_role_allocation_id=role_alloc_id,
                # path_id=path_id
            ).update(stand_status=2, sitting_status=1, come_status=2)

            # 报告席状态为已退席
            BusinessPositionStatus.objects.filter(business_id=bus.id, path_id=path_id,
                                                  position_id=pos['position_id']).update(
                sitting_status=const.SITTING_UP_STATUS,
                business_role_allocation_id=None)

        brast = BusinessRoleAllocationStatus.objects.filter(
            business_id=bus.id,
            business_role_allocation_id=role_alloc_id,
            # path_id=path_id
        ).first()
        image = RoleImage.objects.filter(pk=FlowRoleAllocation.objects.get(pk=bra.flow_role_alloc_id).image_id).first()
        qs_files = RoleImageFile.objects.filter(image=image)
        actors = []
        if origin_pos.actor1:
            actor1 = qs_files.filter(direction=origin_pos.actor1).first()
            actors.append(('/media/' + actor1.file.name) if actor1 and actor1.file else '')
        if origin_pos.actor2:
            actor2 = qs_files.filter(direction=origin_pos.actor2).first()
            actors.append(('/media/' + actor2.file.name) if actor2 and actor2.file else '')

        role_info = {
            'role_alloc_id': role_alloc_id, 'user': user_simple_info(btm.user_id),
            'come_status': brast.come_status, 'sitting_status': brast.sitting_status,
            'stand_status': brast.stand_status,
            'up_btn_status': const.FALSE, 'down_btn_status': const.FALSE,
            'origin_position': origin_position, 'report_position': report_position,
            'actors': actors, 'gender': image.gender if image else 1
        }
        return True, role_info
    except Exception as e:
        logger.exception(u'action_role_end_report Exception:{}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return False, resp


def action_roles_exit(business, node, path_id, user_id):
    """
    送出
    :return:
    """
    try:
        with transaction.atomic():
            brast = BusinessRoleAllocationStatus.objects.filter(
                business_id=business.id,
                business_role_allocation__node_id=node.pk,
                # path_id=path_id,
                sitting_status=2)
            # 报告席
            report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()

            role_alloc_list = []
            for item in brast:
                bra = item.business_role_allocation
                btm = BusinessTeamMember.objects.filter(business_id=business.id, business_role_id=bra.role_id,
                                                        no=bra.no, user_id=user_id).first()
                if btm is None:
                    continue
                report_exists = BusinessReportStatus.objects.filter(business_id=business.pk,
                                                                    business_role_allocation_id=bra.id,
                                                                    path_id=path_id,
                                                                    schedule_status=const.SCHEDULE_UP_STATUS).exists()
                if report_exists:
                    BusinessReportStatus.objects.filter(business_id=business.pk, business_role_allocation_id=bra.id,
                                                        path_id=path_id,
                                                        schedule_status=const.SCHEDULE_UP_STATUS).update(
                        schedule_status=const.SCHEDULE_INIT_STATUS)

                    pos = report_pos
                else:
                    fra = FlowRoleAllocation.objects.filter(pk=bra.flow_role_alloc_id).first()
                    role_position = FlowRolePosition.objects.filter(node_id=node.pk, role_id=fra.role_id,
                                                                    no=fra.no).first()
                    if role_position:
                        pos = FlowPosition.objects.filter(pk=role_position.position_id).first()

                # 占位状态更新
                BusinessPositionStatus.objects.filter(business_id=business.pk, business_role_allocation_id=bra.id,
                                                      path_id=path_id,
                                                      position_id=pos.id).update(sitting_status=1,
                                                                                 business_role_allocation_id=None)
                role_alloc_list.append({
                    'id': bra.id, 'name': bra.role.name, 'no': bra.no, 'code_position': pos.code_position if pos else ''
                })
                item.update(come_status=1, sitting_status=1, stand_status=2)
        return True, role_alloc_list
    except Exception as e:
        logger.exception(u'action_roles_exit Exception:{}'.format(str(e)))
        return False, str(e)


def get_pre_node_path(bus):
    """
    获取上一个环节信息
    :param exp: 实验
    :return:
    """
    try:
        cur_path = BusinessTransPath.objects.filter(business_id=bus.id, node_id=bus.node_id).last()
        if cur_path is None:
            return None
        if cur_path.step == 1:
            return None
        pre_path = BusinessTransPath.objects.filter(business_id=bus.id, step__lt=cur_path.step).last()
        if pre_path is None:
            return None
        return pre_path
    except Exception as e:
        logger.exception(u'get_pre_node_path Exception:{}'.format(str(e)))
        return None


# 当前环节所有角色状态
def action_roles_vote_status(bus, node_id, path):
    sql = '''SELECT t.`business_role_allocation_id` role_alloc_id,t.vote_status, r.`name` role_name,u.`name` user_name
    from t_business_role_allocation_status t
    LEFT JOIN t_business_role_allocation b ON t.business_role_allocation_id=b.id 
    LEFT JOIN t_business_role r ON b.role_id=r.id
    LEFT JOIN t_business_team_member m ON m.role_id=b.role_id and m.no=b.no
    LEFT JOIN t_user u ON m.user_id=u.id
    WHERE t.business_id=%s and b.node_id=%s and t.path_id=%s''' % (bus.pk, node_id, path.pk)
    sql += ' and r.name != \'' + const.ROLE_TYPE_OBSERVER + '\''
    role_status_list = query.select(sql, ['role_alloc_id', 'vote_status', 'role_name', 'user_name'])
    return role_status_list


def get_business_display_files(bus, node_id, path_id):
    """
    实验文件展示列表
    """
    doc_list = []
    if node_id:
        node = FlowNode.objects.filter(pk=node_id).first()
        if node.process.type == 2:
            # 如果是编辑
            # 应用模板
            docs = BusinessDocContent.objects.filter(business_id=bus.pk, node_id=node_id, has_edited=True)
            for d in docs:
                r = tools.generate_code(6)
                doc_list.append({
                    'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                    'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                    'url': '{0}?{1}'.format(d.file.url, r) if d.file else None,
                    'allow_delete': False
                })

            # 提交的文件
            docs = BusinessDoc.objects.filter(business_id=bus.pk, node_id=node_id, path_id=path_id)
            for d in docs:
                sign_list = BusinessDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                doc_list.append({
                    'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                    'signs': list(sign_list), 'url': d.file.url if d.file else None,
                    'allow_delete': True
                })

        elif node.process.type == 3:
            # 如果是展示
            # 获取该环节所有素材id
            doc_ids = list(ProjectDocRole.objects.filter(project_id=bus.project_id,
                                                         node_id=node_id).values_list('doc_id', flat=True))

            if doc_ids:
                doc_ids = list(set(doc_ids))

            # 角色项目素材
            project_docs = ProjectDoc.objects.filter(id__in=doc_ids, usage=4)
            for item in project_docs:
                doc_list.append({
                    'id': item.id, 'filename': item.name, 'url': item.file.url, 'content': item.content,
                    'file_type': item.file_type, 'has_edited': False, 'signs': [],
                    'business_id': bus.pk, 'node_id': node.pk, 'created_by': None,
                    'role_name': '', 'node_name': node.name if node else None,
                    'allow_delete': False
                })

            # 提交的文件
            docs = BusinessDoc.objects.filter(business_id=bus.pk, node_id=node_id, path_id=path_id)
            for d in docs:
                doc_list.append({
                    'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                    'node_id': node.pk, 'created_by': None, 'business_id': bus.pk,
                    'role_name': '', 'node_name': node.name if node else None,
                    'has_edited': False, 'signs': [], 'url': d.file.url if d.file else None,
                    'allow_delete': True
                })

            # 若为模版，判断是否已经编辑
            docs = BusinessDocContent.objects.filter(business_id=bus.pk, node_id=node_id, has_edited=True)
            for d in docs:
                r = tools.generate_code(6)
                doc_list.append({
                    'id': d.doc_id, 'filename': d.name, 'content': d.content,
                    'url': '{0}?{1}'.format(d.file.url, r) if d.file else None, 'file_type': d.file_type,
                    'has_edited': d.has_edited, 'business_id': bus.pk, 'node_id': node.pk, 'created_by': None,
                    'role_name': '', 'node_name': node.name if node else None,
                    'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                })
        else:
            # 环节路径上传文件
            bus_docs = BusinessDoc.objects.filter(business_id=bus.pk, node_id=node_id, path_id=path_id)
            for item in bus_docs:
                node = FlowNode.objects.filter(pk=item.node_id).first()
                role = item.business_role_allocation.role
                sign_list = BusinessDocSign.objects.filter(doc_id=item.pk).values('sign', 'sign_status')
                doc = {
                    'id': item.id, 'filename': item.filename, 'url': item.file.url if item.file else None,
                    'business_id': item.business_id, 'node_id': item.node_id, 'content': item.content,
                    'created_by': user_simple_info(item.created_by_id), 'role_name': role.name if role else '',
                    'signs': list(sign_list), 'node_name': node.name if node else None,
                    'file_type': item.file_type
                }
                doc_list.append(doc)
    else:
        # 已提交文件(不传node_id和path_id)：显示出实验环节中所有上传文件
        bus_docs = BusinessDoc.objects.filter(business_id=bus.pk)
        for item in bus_docs:
            node = FlowNode.objects.filter(pk=item.node_id).first()
            sign_list = BusinessDocSign.objects.filter(doc_id=item.pk).values('sign', 'sign_status')
            doc = {
                'id': item.id, 'filename': item.filename, 'url': item.file.url if item.file else None,
                'business_id': item.business_id, 'node_id': item.node_id, 'content': item.content,
                'created_by': user_simple_info(item.created_by_id), 'role_name': '',
                'signs': list(sign_list), 'node_name': node.name if node else None,
                'file_type': item.file_type
            }
            doc_list.append(doc)

        docs = BusinessDocContent.objects.filter(business_id=bus.pk, has_edited=True)
        for item in docs:
            r = tools.generate_code(6)
            node = FlowNode.objects.filter(pk=item.node_id).first()
            doc_list.append({
                'id': item.doc_id, 'filename': item.name, 'content': item.content,
                'business_id': item.business_id, 'node_id': item.node_id, 'file_type': item.file_type,
                'created_by': user_simple_info(item.created_by_id), 'role_name': '',
                'node_name': node.name if node else None,
                'signs': [{'sign_status': item.sign_status, 'sign': item.sign}],
                'url': '{0}?{1}'.format(item.file.url, r) if item.file else None
            })
    return doc_list


def action_business_jump_start():
    return None


# added by ser
def get_business_display_file_read_status(doc_list, can_terminate, user_id):
    res_list = []
    for item in doc_list:
        doc = item
        if can_terminate is None or can_terminate == 'false':
            btm = BusinessTeamMember.objects.filter(user_id=user_id).first()
            state = BusinessDocTeam.objects.filter(business_doc_id=item["id"], business_team_member_id=btm.pk).first()
        else:
            state = BusinessDocTeam.objects.filter(business_doc_id=item["id"]).first()

        if state is None:
            doc['view_status'] = False
        else:
            doc['view_status'] = True

        res_list.append(doc)
    return res_list

def is_look_on_node(node_id):
    return FlowNode.objects.filter(pk=node_id, look_on=1).exists()


def report_gen(business_id, item, user_id, observable, is_path=True):
    node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first() if is_path else item
    if node.process.type == const.PROCESS_NEST_TYPE:
        return False
    doc_list = []
    vote_status = []
    if node.process.type == 2:
        # 如果是编辑
        # 应用模板
        contents = BusinessDocContent.objects.filter(business_id=business_id, node_id=node.id,
                                                     has_edited=True)
        for d in contents:
            doc_list.append({
                'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                'url': d.file.url if d.file else None
            })
        # 提交的文件
        if is_path:
            docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id,
                                          path_id=item.pk)
        else:
            docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id)
        for d in docs:
            sign_list = BusinessDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
            doc_list.append({
                'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                'signs': list(sign_list), 'url': d.file.url if d.file else None
            })
    elif node.process.type == 3:
        if is_path:
            project_docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id,
                                                  path_id=item.pk)
        else:
            project_docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id)
        for d in project_docs:
            doc_list.append({
                'id': d.id, 'filename': d.filename, 'signs': [],
                'url': d.file.url if d.file else None, 'content': d.content, 'file_type': d.file_type,
            })
    elif node.process.type == 5:
        # 如果是投票   三期 - 增加投票结果数量汇总
        vote_status_0_temp = BusinessRoleAllocationStatus.objects.filter(
            business_id=business_id,
            business_role_allocation__node_id=node.id,
            # path_id=item.id,
            vote_status=0)
        vote_status_0 = []
        # 去掉老师观察者角色的数据
        for item0 in vote_status_0_temp:
            role_alloc_temp = item0.business_role_allocation
            if role_alloc_temp.role.name != const.ROLE_TYPE_OBSERVER:
                vote_status_0.append(item0)

        vote_status_1_temp = BusinessRoleAllocationStatus.objects.filter(
            business_id=business_id,
            business_role_allocation__node_id=node.id,
            # path_id=item.id,
            vote_status=1)
        vote_status_1 = []
        # 去掉老师观察者角色的数据
        for item1 in vote_status_1_temp:
            role_alloc_temp = item1.business_role_allocation
            if role_alloc_temp.name != const.ROLE_TYPE_OBSERVER:
                vote_status_1.append(item1)

        vote_status_2_temp = BusinessRoleAllocationStatus.objects.filter(
            business_id=business_id,
            business_role_allocation__node_id=node.id,
            # path_id=item.id,
            vote_status=2)
        vote_status_2 = []
        # 去掉老师观察者角色的数据
        for item2 in vote_status_2_temp:
            role_alloc_temp = item2.business_role_allocation
            if role_alloc_temp.name != const.ROLE_TYPE_OBSERVER:
                vote_status_2.append(item2)

        vote_status_9_temp = BusinessRoleAllocationStatus.objects.filter(
            business_id=business_id,
            business_role_allocation__node_id=node.id,
            # path_id=item.id,
            vote_status=9)
        vote_status_9 = []
        # 去掉老师观察者角色的数据
        for item9 in vote_status_9_temp:
            role_alloc_temp = item9.business_role_allocation
            if role_alloc_temp.name != const.ROLE_TYPE_OBSERVER:
                vote_status_9.append(item9)
        vote_status = [{'status': '同意', 'num': len(vote_status_1)},
                       {'status': '不同意', 'num': len(vote_status_2)},
                       {'status': '弃权', 'num': len(vote_status_9)},
                       {'status': '未投票', 'num': len(vote_status_0)}]
        pass
    else:
        # 提交的文件
        if is_path:
            docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id,
                                          path_id=item.id)
        else:
            docs = BusinessDoc.objects.filter(business_id=business_id, node_id=node.id)
        for d in docs:
            sign_list = BusinessDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
            doc_list.append({
                'id': d.id, 'filename': d.filename, 'content': d.content,
                'signs': list(sign_list), 'url': d.file.url if d.file else None, 'file_type': d.file_type
            })

    # 消息
    if is_path:
        messages = BusinessMessage.objects.filter(business_id=business_id,
                                              business_role_allocation__node_id=node.id,
                                              path_id=item.id).order_by('timestamp')
    else:
        messages = BusinessMessage.objects.filter(business_id=business_id,
                                                  business_role_allocation__node_id=node.id).order_by('timestamp')
    message_list = []
    for m in messages:
        message = {
            'user_name': m.user_name, 'role_name': m.role_name,
            'msg': m.msg, 'msg_type': m.msg_type, 'ext': json.loads(m.ext),
            'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        message_list.append(message)

    # 个人笔记
    note = BusinessNotes.objects.filter(business_id=business_id,
                                        node_id=node.id,
                                        created_by_id=user_id).first() if observable == False else None
    return {
        'docs': doc_list, 'messages': message_list, 'id': node.id, 'node_name': node.name,
        'note': note.content if note else None, 'type': node.process.type if node.process else 0,
        'vote_status': vote_status
    }