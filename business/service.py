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
    FlowProcess, ProcessAction, FlowDocs, FlowNodeDocs, FlowRoleAllocation
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
                'alloc_id': roleAlloc.id, 'come_status': roleAllocStatus.come_status, 'no': roleAlloc.no,
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
    btmQs = BusinessTeamMember.objects.filter(business=business, user=user)
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
    business_role_allocs = BusinessRoleAllocation.objects.filter(business=business, project_id=business.cur_project_id,
                                                                 can_take_in=True)
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


def get_business_display_files(business, node_id, path_id):
    """
    实验文件展示列表
    """
    doc_list = []
    if node_id:
        node = FlowNode.objects.filter(pk=node_id).first()
        if node.process.type == 2:
            # 如果是编辑
            # 应用模板
            docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id, has_edited=True)
            for d in docs:
                r = tools.generate_code(6)
                doc_list.append({
                    'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                    'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                    'url': '{0}?{1}'.format(d.file.url, r) if d.file else None,
                    'allow_delete': False
                })

            # 提交的文件
            docs = BusinessDoc.objects.filter(business_id=business.pk, node_id=node_id, path_id=path_id)
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
            doc_ids = list(ProjectDocRole.objects.filter(project_id=business.project_id,
                                                         node_id=node_id).values_list('doc_id', flat=True))

            if doc_ids:
                doc_ids = list(set(doc_ids))

            # 角色项目素材
            project_docs = ProjectDoc.objects.filter(id__in=doc_ids, usage=4)
            for item in project_docs:
                doc_list.append({
                    'id': item.id, 'filename': item.name, 'url': item.file.url, 'content': item.content,
                    'file_type': item.file_type, 'has_edited': False, 'signs': [],
                    'business_id': business.pk, 'node_id': node.pk, 'created_by': None,
                    'role_name': '', 'node_name': node.name if node else None,
                    'allow_delete': False
                })

            # 提交的文件
            docs = BusinessDoc.objects.filter(business_id=business.pk, node_id=node_id, path_id=path_id)
            for d in docs:
                doc_list.append({
                    'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                    'node_id': node.pk, 'created_by': None, 'business_id': business.pk,
                    'role_name': '', 'node_name': node.name if node else None,
                    'has_edited': False, 'signs': [], 'url': d.file.url if d.file else None,
                    'allow_delete': True
                })

            # 若为模版，判断是否已经编辑
            docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id, has_edited=True)
            for d in docs:
                r = tools.generate_code(6)
                doc_list.append({
                    'id': d.doc_id, 'filename': d.name, 'content': d.content,
                    'url': '{0}?{1}'.format(d.file.url, r) if d.file else None, 'file_type': d.file_type,
                    'has_edited': d.has_edited, 'business_id': business.pk, 'node_id': node.pk, 'created_by': None,
                    'role_name': '', 'node_name': node.name if node else None,
                    'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                })
        else:
            # 环节路径上传文件
            business_docs = BusinessDoc.objects.filter(business_id=business.pk, node_id=node_id, path_id=path_id)
            for item in business_docs:
                node = FlowNode.objects.filter(pk=item.node_id).first()
                role = ProjectRole.objects.filter(pk=item.role_id).first()
                sign_list = BusinessDocSign.objects.filter(doc_id=item.pk).values('sign', 'sign_status')
                doc = {
                    'id': item.id, 'filename': item.filename, 'url': item.file.url if item.file else None,
                    'node_id': item.node_id, 'content': item.content,
                    'created_by': user_simple_info(item.created_by), 'role_name': role.name if role else '',
                    'signs': list(sign_list), 'node_name': node.name if node else None,
                    'file_type': item.file_type
                }
                doc_list.append(doc)
    else:
        # 已提交文件(不传node_id和path_id)：显示出实验环节中所有上传文件
        business_docs = BusinessDoc.objects.filter(business_id=business.pk)
        for item in business_docs:
            node = FlowNode.objects.filter(pk=item.node_id).first()
            sign_list = BusinessDocSign.objects.filter(doc_id=item.pk).values('sign', 'sign_status')
            doc = {
                'id': item.id, 'filename': item.filename, 'url': item.file.url if item.file else None,
                'node_id': item.node_id, 'content': item.content,
                'created_by': user_simple_info(item.created_by), 'role_name': '',
                'signs': list(sign_list), 'node_name': node.name if node else None,
                'file_type': item.file_type
            }
            doc_list.append(doc)

        docs = BusinessDocContent.objects.filter(business_id=business.pk, has_edited=True)
        for item in docs:
            r = tools.generate_code(6)
            node = FlowNode.objects.filter(pk=item.node_id).first()
            doc_list.append({
                'id': item.doc_id, 'filename': item.name, 'content': item.content,
                'business_id': item.business_id, 'node_id': item.node_id, 'file_type': item.file_type,
                'created_by': user_simple_info(item.created_by), 'role_name': '',
                'node_name': node.name if node else None,
                'signs': [{'sign_status': item.sign_status, 'sign': item.sign}],
                'url': '{0}?{1}'.format(item.file.url, r) if item.file else None
            })
    return doc_list


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


def get_business_templates(business, node_id, role_alloc_id, usage, pra=None):
    doc_list = []
    try:

        """
        实验模板
        """
        if role_alloc_id and pra is None:
            bra = BusinessRoleAllocation.objects.filter(pk=role_alloc_id).first()
            pra = ProjectRoleAllocation.objects.filter(pk=bra.project_role_alloc_id).first()

        if usage and usage == '3':
            docs = BusinessDocContent.objects.filter(business_id=business.pk, node_id=node_id,
                                                     business_role_allocation_id=role_alloc_id)
            for item in docs:
                doc_list.append({
                    'id': item.id, 'name': item.name, 'type': '', 'usage': 3,
                    'content': item.content, 'file_type': item.file_type,
                    'has_edited': item.has_edited, 'from': 1,
                    'sign_status': item.sign_status, 'sign': item.sign,
                    'role_alloc_id': item.business_role_allocation_id, 'url': item.file.url
                })
        else:
            if role_alloc_id:
                doc_ids = ProjectDocRole.objects.filter(project_id=business.cur_project_id, node_id=node_id,
                                                        role_id=pra.role_id, no=pra.no).values_list('doc_id', flat=True)
            else:
                doc_ids = ProjectDocRole.objects.filter(project_id=business.cur_project_id,
                                                        node_id=node_id).values_list('doc_id', flat=True)

            qs = ProjectDoc.objects.filter(project_id=business.cur_project_id)
            if usage:
                qs = qs.filter(usage=usage)
            if node_id:
                qs = qs.filter(id__in=doc_ids)
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
        
def get_all_roles_status(bus, project, node, path):
    """
    所有角色
    """
    key = tools.make_key(const.CACHE_ALL_ROLES_STATUS, '%s:%s:%s' % (bus.pk, node.pk, path.pk), 1)
    data = cache.get(key)
    if data:
        return data
    else:
        # 报告席
        report_pos = FlowPosition.objects.filter(process=node.process, type=const.SEAT_REPORT_TYPE).first()
        report_status = ExperimentReportStatus.objects.filter(experiment_id=bus.pk, node_id=node.pk,
                                                              path_id=path.pk,
                                                              schedule_status=const.SCHEDULE_UP_STATUS).first()

        sql = '''SELECT t.role_id,t.come_status,t.sitting_status,t.stand_status,t.vote_status,
                t.show_status,t.speak_times,r.`name` role_name,r.flow_role_id,u.name,r.image_id,i.gender
                from t_experiment_role_status t
                LEFT JOIN t_project_role r ON t.role_id=r.id
                LEFT JOIN t_user u ON t.user_id=u.id
                LEFT JOIN t_role_image i ON i.id=r.image_id
                WHERE t.experiment_id=%s and t.node_id=%s and t.path_id=%s''' % (bus.pk, node.pk, path.pk)
        sql += ' order by t.sitting_status '
        logger.info(sql)
        role_list = query.select(sql, ['role_id', 'come_status', 'sitting_status', 'stand_status',
                                       'vote_status', 'show_status', 'speak_times', 'role_name', 'flow_role_id',
                                       'user_name', 'image_id', 'gender'])
        for i in range(0, len(role_list)):
            role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node.pk,
                                                            role_id=role_list[i]['flow_role_id']).first()
            actors = []
            if role_position:
                qs_files = RoleImageFile.objects.filter(image_id=role_list[i]['image_id'])
                if report_pos and report_status:
                    if role_list[i]['role_id'] == report_status.role_id:
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
        cache.set(key, role_list)
        return role_list
