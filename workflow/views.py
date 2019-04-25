#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging
import xlwt, xlrd
from docx import Document

from account.models import Tuser
from django.shortcuts import redirect
from course.models import CourseClass
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from django.utils.http import urlquote
from account.service import user_simple_info
from experiment.models import Experiment
from project.models import Project, ProjectRole
from system.views import file_info
from team.models import Team
from utils import code, const, public_fun, tools
from utils.request_auth import auth_check
from project.models import ProjectJump
from workflow.models import Flow, FlowNode, FlowTrans, FlowProcess, FlowDocs, FlowRole, FlowRoleAllocation, \
    FlowRoleActionNew, FlowRolePosition, RoleImage, RoleImageType, FlowNodeDocs, FlowAction, FlowPosition, \
    ProcessRoleActionNew, ProcessAction
from workflow.service import bpmn_parse, flow_nodes, get_end_node, flow_doc_save

logger = logging.getLogger(__name__)


# 场景站位列表
def api_workflow_process_positions(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        process_id = request.GET.get("process_id", None)  # 环节ID

        postions = FlowPosition.objects.filter(process_id=process_id, type=0, del_flag=0)

        position_list = []
        for item in postions:
            position_list.append({
                'id': item.id, 'position': item.position, 'code_position': item.code_position
            })

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = position_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_flow_draw Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 动作设置信息
def api_workflow_role_action(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id", None)  # 流程ID
        flow = Flow.objects.filter(pk=flow_id).first()

        if flow:
            flow_role_allocation = FlowRoleAllocation.objects.filter(flow_id=flow_id, del_flag=0)

            action_allocations = []
            for item in flow_role_allocation:
                # 流程环节角色动作
                flow_actions = FlowRoleActionNew.objects.filter(flow_id=flow_id, node_id=item.node_id,
                                                                role_id=item.role_id, del_flag=0).first()
                flow_action_ids = []
                if flow_actions and flow_actions.actions:
                    flow_action_ids = json.loads(flow_actions.actions)
                action_allocations.append({
                    'node_id': item.node_id, 'role_id': item.role_id, 'role_name': item.role.name,
                    'role_type': item.role.type, 'flow_action_ids': flow_action_ids
                })

            actions = FlowAction.objects.filter(del_flag=0)
            flow_actions = []
            for item in actions:
                flow_actions.append({
                    'id': item.id, 'name': item.name
                })

            node_list = []
            nodes = FlowNode.objects.filter(flow_id=flow_id)

            for item in nodes:
                if item.process:
                    process = {
                        'id': item.process.id, 'name': item.process.name, 'type': item.process.type,
                        'file': item.process.file.url if item.process.file else None,
                        'image': item.process.image.url if item.process.image else None,
                    }
                else:
                    process = None
                node_list.append({
                    'id': item.id, 'name': item.name, 'process': process
                })

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'flow_actions': flow_actions, 'nodes': node_list, 'action_allocations': action_allocations}
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_role_action Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 功能动作列表
def api_workflow_flow_actions(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        actions = FlowAction.objects.filter(del_flag=0).all()
        action_list = []
        for item in actions:
            action = {'id': item.id, 'name': item.name, 'cmd': item.cmd}
            action_list.append(action)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = action_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_flow_draw Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 动作设置信息
def api_workflow_role_process_action(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id", None)  # 流程ID
        flow = Flow.objects.filter(pk=flow_id).first()

        if flow:
            flow_role_allocation = FlowRoleAllocation.objects.filter(flow_id=flow_id, del_flag=0)

            action_allocations = []
            for item in flow_role_allocation:
                # 流程环节角色场景动画
                actions = ProcessRoleActionNew.objects.filter(flow_id=flow_id, node_id=item.node_id,
                                                              role_id=item.role_id, del_flag=0).first()
                process_action_ids = []
                if actions and actions.actions:
                    process_action_ids = json.loads(actions.actions)

                action_allocations.append({
                    'node_id': item.node_id, 'role_id': item.role_id, 'role_name': item.role.name,
                    'role_type': item.role.type, 'process_action_ids': process_action_ids
                })

            node_list = []
            nodes = FlowNode.objects.filter(flow_id=flow_id)

            for item in nodes:
                if item.process:
                    actions = ProcessAction.objects.filter(process=item.process, del_flag=0).values('id', 'name')
                    process = {
                        'id': item.process.id, 'name': item.process.name, 'type': item.process.type,
                        'file': item.process.file.url if item.process.file else None,
                        'image': item.process.image.url if item.process.image else None,
                        'process_actions': list(actions)
                    }
                else:
                    process = None
                node_list.append({
                    'id': item.id, 'name': item.name, 'process': process
                })

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'nodes': node_list, 'action_allocations': action_allocations}
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_role_process_action Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def is_equal_old_flow(flow_id, nodes, trans):
    if FlowNode.objects.filter(flow_id=flow_id, del_flag=0).count() != len(nodes):
        return False
    for node in nodes:
        if not FlowNode.objects.filter(flow_id=flow_id, task_id=node['id']).exists():
            return False

    if FlowTrans.objects.filter(flow_id=flow_id, del_flag=0).count() != len(trans):
        return False

    for tran in trans:
        if not FlowTrans.objects.filter(flow_id=flow_id, sequence_flow_id=tran['id']).exists():
            return False
    return True


# 画图
def api_workflow_flow_draw(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 流程ID
        xml = request.POST.get("xml", None)  # 流程图xml

        if flow_id is None or xml is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id, created_by=request.user.id).first()
        if flow:
            if flow.status == 2:
                resp = code.get_msg(code.FLOW_HAS_PUBLISHED)
            else:
                # 从流程图xml中获取环节和流转信息
                nodes, trans = bpmn_parse(xml.encode('utf-8'))
                has_start_node = False

                # 判断流程图是否有开始节点
                for tran in trans:
                    if tran['sourceRef'].startswith('StartEvent'):
                        has_start_node = True
                        break
                    else:
                        continue
                if not has_start_node:
                    resp = code.get_msg(code.FLOW_CHART_ERROR)
                else:
                    # 验证流程图结构是否变化
                    exists_node = FlowNode.objects.filter(flow_id=flow_id, del_flag=0).exists()
                    if exists_node and not is_equal_old_flow(flow_id, nodes, trans):
                        # 删除之前创建的环节和流转信息,相关配置信息
                        FlowNode.objects.filter(flow_id=flow_id).delete()
                        FlowTrans.objects.filter(flow_id=flow_id).delete()
                        FlowRole.objects.filter(flow_id=flow_id).delete()
                        FlowDocs.objects.filter(flow_id=flow_id).delete()
                        FlowNodeDocs.objects.filter(flow_id=flow_id).delete()
                        FlowRoleAllocation.objects.filter(flow_id=flow_id).delete()
                        FlowRolePosition.objects.filter(flow_id=flow_id).delete()

                    with transaction.atomic():
                        exists_node = FlowNode.objects.filter(flow_id=flow_id, del_flag=0).exists()
                        if exists_node:
                            flow.xml = xml
                            flow.save()
                            # 修改环节信息
                            for node in nodes:
                                FlowNode.objects.filter(flow_id=flow_id, task_id=node['id']).update(name=node['name'])

                            # 修改环节流转信息
                            for tran in trans:
                                if 'name' in tran:
                                    name = tran['name']
                                else:
                                    name = None
                                FlowTrans.objects.filter(flow_id=flow_id,
                                                         sequence_flow_id=tran['id']).update(incoming=tran['sourceRef'],
                                                                                             outgoing=tran['targetRef'],
                                                                                             name=name)
                        else:
                            # 新建
                            flow.xml = xml
                            flow.step = const.FLOW_STEP_0
                            flow.save()

                            # 保存环节信息
                            node_list = []
                            for node in nodes:
                                node_list.append(FlowNode(flow_id=flow_id, name=node['name'], task_id=node['id']))
                            FlowNode.objects.bulk_create(node_list)

                            # 环节流转信息
                            tran_list = []
                            for tran in trans:
                                if 'name' in tran:
                                    name = tran['name']
                                else:
                                    name = None
                                tran_list.append(
                                    FlowTrans(flow_id=flow_id, incoming=tran['sourceRef'], outgoing=tran['targetRef'],
                                              sequence_flow_id=tran['id'], name=name))
                            FlowTrans.objects.bulk_create(tran_list)
                    resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.METHOD_NOT_ALLOW)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_flow_draw Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.FLOW_CHART_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色分配信息
def api_workflow_role_allcation(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id")  # 流程ID
        flow = Flow.objects.filter(pk=flow_id, del_flag=0).first()

        if flow:
            nodes = FlowNode.objects.filter(flow_id=flow_id, del_flag=0)
            node_list = []
            for item in nodes:
                allocation_list = []
                if item.process.type == 1:
                    # 环节角色分配
                    ra_list = FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=item.id, del_flag=0)
                    for r in ra_list:
                        # 占位数据
                        role_position = FlowRolePosition.objects.filter(flow_id=flow_id, node_id=item.id,
                                                                        role_id=r.role_id, del_flag=0).first()
                        position_id = role_position.position_id if role_position else None
                        allocation_list.append({
                            'role_id': r.role_id, 'role_name': r.role.name,
                            'position_id': position_id, 'role_type': r.role.type
                        })
                node_list.append({
                    'id': item.id, 'name': item.name,
                    'process': {'id': item.process.pk, 'type': item.process.type,
                                'name': item.process.name if item.process else None,
                                'image': item.process.image.url if item.process.image else None},
                    'allocation_list': allocation_list
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = node_list
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_role_allocation Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色分配信息
def api_workflow_role_assign_info(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id")  # 流程ID
        flow = Flow.objects.filter(pk=flow_id, del_flag=0).first()

        if flow:
            nodes = FlowNode.objects.filter(flow_id=flow_id, del_flag=0)
            node_list = []
            for item in nodes:
                if item.process is None:
                    resp = code.get_msg(code.FLOW_PROCESS_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                node_list.append({
                    'id': item.id, 'name': item.name,
                    'type': item.process.type if item.process else None,
                    'process_name': item.process.name if item.process else None,
                    'image': item.process.image.url if item.process.image else None
                })

            roles = FlowRole.objects.filter(flow_id=flow_id, del_flag=0)
            role_list = []
            for item in roles:
                allocations = FlowRoleAllocation.objects.filter(flow_id=flow_id, role_id=item.id, del_flag=0)
                allocation_list = []
                for a in allocations:
                    role_position = FlowRolePosition.objects.filter(flow_id=flow_id, node_id=a.node_id,
                                                                    role_id=item.id).first()
                    position_id = role_position.position_id if role_position else None
                    allocation_list.append({
                        'node_id': a.node_id, 'can_terminate': a.can_terminate,
                        'can_brought': a.can_brought, 'position_id': position_id
                    })
                if item.name != const.ROLE_TYPE_OBSERVER:
                    role_list.append({
                        'role_id': item.id, 'role_name': item.name, 'role_type': item.type,
                        'assign_info': allocation_list
                    })
            types = list(set(roles.values_list('type', flat=True)))
            if const.ROLE_TYPE_OBSERVER in types:
                types.remove(const.ROLE_TYPE_OBSERVER)
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'nodes': node_list, 'roles': role_list, 'role_types': types
            }
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_node_roles Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程素材列表
def api_workflow_doc_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id", None)  # 流程ID
        flow = Flow.objects.filter(pk=flow_id, del_flag=0).first()

        if flow:
            qs = FlowDocs.objects.filter(flow_id=flow_id, del_flag=0)
            doc_list = []
            for item in qs:
                node_ids = set(
                    FlowNodeDocs.objects.filter(flow_id=flow_id, doc_id=item.id,
                                                del_flag=0).values_list('node_id', flat=True))
                doc = {
                    'id': item.id, 'name': item.name, 'usage': item.usage, 'file_type': item.file_type,
                    'file': item.file.url if item.file else None, 'type': item.type,
                    'content': item.content, 'node_ids': list(node_ids)
                }
                doc_list.append(doc)
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'doc_list': doc_list, 'nodes': flow_nodes(flow.id)}
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_doc_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程角色列表
def api_workflow_role_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id")  # 流程ID
        flow = Flow.objects.filter(pk=flow_id).first()

        if flow:
            qs = FlowRole.objects.filter(flow_id=flow_id, del_flag=0).all()
            types = list(set(qs.values_list('type', flat=True)))
            if const.ROLE_TYPE_OBSERVER in types:
                types.remove(const.ROLE_TYPE_OBSERVER)

            role_list = []
            for role in qs:
                obj = RoleImage.objects.get(pk=role.image_id)
                if obj:
                    img = {'id': obj.id, 'name': obj.name, 'file': obj.avatar.url if obj.avatar else None,
                           'gender': obj.gender}
                else:
                    img = None
                if role.type != const.ROLE_TYPE_OBSERVER:
                    role_list.append({
                        'id': role.id, 'name': role.name, 'min': role.min, 'max': role.max, 'category': role.category,
                        'type': role.type, 'image': img
                    })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'roles': role_list, 'flow_role_types': types}
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_role_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程环节列表
def api_workflow_node_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get("flow_id")  # 流程ID
        flow = Flow.objects.filter(pk=flow_id).first()

        if flow:
            qs = FlowNode.objects.filter(flow_id=flow_id, del_flag=0).all()
            node_list = []

            for node in qs:
                if node.process:
                    process = {
                        'id': node.process.id, 'name': node.process.name, 'type': node.process.type,
                        'image': node.process.image.url if node.process.image else None
                    }
                else:
                    process = None
                node_list.append({
                    'id': node.id, 'name': node.name, 'look_on': node.look_on, 'step': node.step,
                    'task_id': node.task_id,
                    'condition': node.condition, 'process': process
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = node_list
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_node_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色形象列表
def api_workflow_role_image_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        types = RoleImageType.objects.all()

        role_list = []
        for item in types:
            type_dict = {'id': item.id, 'name': item.name, 'roles': []}
            roles = RoleImage.objects.filter(type_id=item.id)
            for role in roles:
                type_dict['roles'].append(
                    {'id': role.id, 'name': role.name, 'gender': role.gender,
                     'avatar': role.avatar.url if role.avatar else None})
            role_list.append(type_dict)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = role_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_role_image_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 复制流程
def api_workflow_flow_copy(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id")  # 流程ID
        name = request.POST.get("name")  # 名称

        # 验证流程名称是否唯一
        if Flow.objects.filter(name=name, del_flag=0).exists():
            resp = code.get_msg(code.FLOW_SAME_NAME_HAS_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id).first()
        if flow:
            with transaction.atomic():
                instance = Flow.objects.create(name=name, animation1=flow.animation1, animation2=flow.animation2,
                                               type_label=flow.type_label, task_label=flow.task_label, step=flow.step,
                                               copy_from=flow_id, xml=flow.xml, created_by=request.user.id)
                # 复制环节流转信息
                trans = FlowTrans.objects.filter(flow_id=flow_id)
                tran_list = []
                for tran in trans:
                    tran_list.append(FlowTrans(name=tran.name, flow_id=instance.id,
                                               sequence_flow_id=tran.sequence_flow_id, conditions=tran.conditions,
                                               incoming=tran.incoming, outgoing=tran.outgoing))
                FlowTrans.objects.bulk_create(tran_list)

                # 对应源新环节和角色id
                node_map = []
                role_map = []
                docs_map = []
                # 复制环节信息
                nodes = FlowNode.objects.filter(flow_id=flow_id)
                for node in nodes:
                    new = FlowNode.objects.create(flow_id=instance.id, name=node.name, task_id=node.task_id,
                                                  condition=node.condition, process=node.process, look_on=node.look_on,
                                                  step=node.step)
                    node_map.append((node.id, new.id))

                # 复制角色信息
                roles = FlowRole.objects.filter(flow_id=flow_id, del_flag=0)
                for role in roles:
                    new = FlowRole.objects.create(flow_id=instance.id, image_id=role.image_id, name=role.name,
                                                  type=role.type, min=role.min, max=role.max, category=role.category)
                    role_map.append((role.id, new.id))

                # 复制素材信息
                docs = FlowDocs.objects.filter(flow_id=flow_id, del_flag=0)
                for doc in docs:
                    new = FlowDocs.objects.create(flow_id=instance.id, name=doc.name, type=doc.type, usage=doc.usage,
                                                  content=doc.content, file=doc.file, file_type=doc.file_type)
                    docs_map.append((doc.id, new.id))
                # logger.info(node_map)
                # logger.info(role_map)
                # logger.info(docs_map)

                # 复制流程环节素材分配
                node_docs_list = []
                node_docs = FlowNodeDocs.objects.filter(flow_id=flow_id, del_flag=0)
                for item in node_docs:
                    new_node_id = public_fun.get_map(node_map, item.node_id)
                    new_doc_id = public_fun.get_map(docs_map, item.doc_id)
                    if new_node_id is None or new_doc_id is None:
                        continue
                    # logger.info('item.doc_id:%s,new_doc_id:%s' % (item.doc_id, new_doc_id))
                    node_docs_list.append(FlowNodeDocs(flow_id=instance.id, node_id=new_node_id, doc_id=new_doc_id))
                FlowNodeDocs.objects.bulk_create(node_docs_list)

                # 复制环节角色分配
                role_allocations = FlowRoleAllocation.objects.filter(flow_id=flow_id, del_flag=0)
                role_allocation_list = []
                for item in role_allocations:
                    new_node_id = public_fun.get_map(node_map, item.node.id)
                    new_role_id = public_fun.get_map(role_map, item.role.id)
                    if new_node_id is None or new_role_id is None:
                        continue
                    role_allocation_list.append(FlowRoleAllocation(flow=instance,
                                                                   node_id=new_node_id,
                                                                   role_id=new_role_id,
                                                                   can_terminate=item.can_terminate,
                                                                   can_brought=item.can_brought))
                FlowRoleAllocation.objects.bulk_create(role_allocation_list)

                # 复制角色动作和动画设置
                role_actions = FlowRoleActionNew.objects.filter(flow_id=flow_id, del_flag=0)
                role_action_list = []
                for item in role_actions:
                    new_node_id = public_fun.get_map(node_map, item.node.id)
                    new_role_id = public_fun.get_map(role_map, item.role.id)
                    if new_node_id is None or new_role_id is None:
                        continue
                    role_action_list.append(FlowRoleActionNew(flow=instance, node_id=new_node_id, role_id=new_role_id,
                                                              actions=item.actions))
                FlowRoleActionNew.objects.bulk_create(role_action_list)

                process_actions = ProcessRoleActionNew.objects.filter(flow_id=flow_id, del_flag=0)
                process_action_list = []
                for item in process_actions:
                    new_node_id = public_fun.get_map(node_map, item.node.id)
                    new_role_id = public_fun.get_map(role_map, item.role.id)
                    if new_node_id is None or new_role_id is None:
                        continue
                    if item.actions is None:
                        continue

                    process_action_list.append(ProcessRoleActionNew(flow=instance, node_id=new_node_id,
                                                                    role_id=new_role_id, actions=item.actions))
                ProcessRoleActionNew.objects.bulk_create(process_action_list)

                # 复制角色站位
                role_positions = FlowRolePosition.objects.filter(flow_id=flow_id, del_flag=0)
                role_position_list = []
                for item in role_positions:
                    new_node_id = public_fun.get_map(node_map, item.node_id)
                    new_role_id = public_fun.get_map(role_map, item.role_id)
                    if new_node_id is None or new_role_id is None:
                        continue
                    role_position_list.append(FlowRolePosition(flow_id=instance.id,
                                                               node_id=new_node_id,
                                                               role_id=new_role_id,
                                                               position_id=item.position_id))
                FlowRolePosition.objects.bulk_create(role_position_list)

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': instance.id, 'name': instance.name, 'xml': instance.xml, 'step': instance.step,
                    'animation1': file_info(instance.animation1),
                    'animation2': file_info(instance.animation2),
                    'created_by': user_simple_info(instance.created_by),
                    'create_time': instance.create_time.strftime('%Y-%m-%d'),
                    'task_label': instance.task_label,
                    'status': instance.status, 'type_label': instance.type_label
                }
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_flow_copy Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色站位设置{"node_id":2561,"role_id":1158,"position_id":41}
def api_workflow_roles_position_setup(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        node_id = request.POST.get("node_id", None)
        role_id = request.POST.get("role_id", None)
        position_id = request.POST.get("position_id", None)
        logger.info('flow_id:%s,node_id:%s,role_id:%s,position_id:%s' % (flow_id, node_id, role_id, position_id))

        if flow_id:
            FlowRolePosition.objects.update_or_create(flow_id=flow_id, node_id=node_id, role_id=role_id,
                                                      defaults={'position_id': position_id, 'del_flag': 0})
            resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_position_setup Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色站位设置
def api_workflow_roles_position(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)

        if flow_id:
            flow = Flow.objects.get(pk=flow_id)
            if flow.step < const.FLOW_STEP_7:
                flow.step = const.FLOW_STEP_7
                flow.save()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_position Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色动作设置
def api_workflow_roles_action(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        node_id = request.POST.get('node_id', None)
        data = request.POST.get("data", None)  # 动作设置信息

        if data and flow_id:
            flow = Flow.objects.get(pk=flow_id)
            node = FlowNode.objects.get(pk=node_id)
            action_list = json.loads(data)

            new_actions = []
            with transaction.atomic():
                for item in action_list:
                    obj = FlowRoleActionNew.objects.filter(flow_id=flow_id, node_id=node_id,
                                                           role_id=item['role_id']).first()
                    if obj:
                        if obj.actions:
                            actions = json.loads(obj.actions)
                        else:
                            actions = []
                        # 选中
                        if item['selected']:
                            if item['action_id'] not in actions:
                                actions.append(item['action_id'])
                        else:
                            if item['action_id'] in actions:
                                actions.remove(item['action_id'])
                        obj.actions = actions
                        obj.del_flag = const.DELETE_FLAG_NO
                        obj.save(update_fields=['actions', 'del_flag'])

                    else:
                        if item['selected']:
                            if node.process and node.process.type == 1:
                                new_actions.append(FlowRoleActionNew(flow_id=flow_id, node_id=node_id,
                                                                     role_id=item['role_id'],
                                                                     actions=[item['action_id']]))

                if new_actions:
                    FlowRoleActionNew.objects.bulk_create(new_actions)

                if flow.step < const.FLOW_STEP_5:
                    flow.step = const.FLOW_STEP_5
                    flow.save()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_action Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色动画设置
def api_workflow_roles_process_action(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        node_id = request.POST.get('node_id', None)
        data = request.POST.get("data", None)  # 动画设置信息
        # logger.info(data)
        if data and flow_id:
            flow = Flow.objects.get(pk=flow_id)
            node = FlowNode.objects.get(pk=node_id)
            action_list = json.loads(data)
            new_actions = []
            with transaction.atomic():
                for item in action_list:
                    obj = ProcessRoleActionNew.objects.filter(flow_id=flow_id, node_id=node_id,
                                                              role_id=item['role_id']).first()
                    if obj:
                        if obj.actions:
                            actions = json.loads(obj.actions)
                        else:
                            actions = []
                        # 选中
                        if item['selected']:
                            if item['action_id'] not in actions:
                                actions.append(item['action_id'])
                        else:
                            if item['action_id'] in actions:
                                actions.remove(item['action_id'])
                        obj.actions = actions
                        obj.del_flag = const.DELETE_FLAG_NO
                        obj.save(update_fields=['actions', 'del_flag'])
                    else:
                        if item['selected']:
                            if node.process and node.process.type == 1:
                                new_actions.append(ProcessRoleActionNew(flow_id=flow_id, node_id=node_id,
                                                                        role_id=item['role_id'],
                                                                        actions=[item['action_id']]))
                if new_actions:
                    ProcessRoleActionNew.objects.bulk_create(new_actions)

                if flow.step < const.FLOW_STEP_6:
                    flow.step = const.FLOW_STEP_6
                    flow.save()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_process_action Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程角色分配并初始全选动作设置
def api_workflow_roles_allocate(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        node_id = request.POST.get('node_id', None)
        data = request.POST.get("data", None)  # 分配信息

        if data and flow_id:
            flow = Flow.objects.get(pk=flow_id)
            node = FlowNode.objects.get(pk=node_id)
            allocation = json.loads(data)

            # 全选环节场景功能动作
            flow_actions = []
            if allocation:
                actions_list = FlowAction.objects.filter(del_flag=0).values_list('id', flat=True)
                for d in actions_list:
                    flow_actions.append(int(d))

            new_allocations = []
            new_actions = []
            with transaction.atomic():
                for item in allocation:
                    # 选中
                    if item['selected']:
                        if FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=node_id,
                                                             role_id=item['role_id']).exists():
                            # if FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=node_id,
                            #                                      role_id=item['role_id'],
                            #                                      can_terminate=item['can_terminate']).exists():
                            #     resp = code.get_msg(code.SYSTEM_ERROR)
                            #     return HttpResponse(json.dumps(resp, ensure_ascii=False),
                            #                         content_type="application/json")
                            FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=node_id,
                                                              role_id=item['role_id']).update(
                                can_terminate=item['can_terminate'],
                                can_brought=item['can_brought'],
                                del_flag=0)
                        else:
                            new_allocations.append(FlowRoleAllocation(flow_id=flow_id, node_id=node_id,
                                                                      role_id=item['role_id'],
                                                                      can_terminate=item['can_terminate'],
                                                                      can_brought=item['can_brought']))

                        if node.process and node.process.type == 1:
                            # 全选环节功能动作，如果不存在则创建
                            if not FlowRoleActionNew.objects.filter(flow_id=flow_id, node_id=node_id,
                                                                    role_id=item['role_id']).exists():
                                new_actions.append(FlowRoleActionNew(flow_id=flow_id, node_id=node_id,
                                                                     role_id=item['role_id'],
                                                                     actions=flow_actions))
                    else:
                        # 取消选择
                        FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=node_id,
                                                          role_id=item['role_id']).update(
                            del_flag=const.DELETE_FLAG_YES)
                if new_allocations:
                    FlowRoleAllocation.objects.bulk_create(new_allocations)
                if new_actions:
                    FlowRoleActionNew.objects.bulk_create(new_actions)

                exists = FlowRoleAllocation.objects.filter(flow_id=flow_id).exists()
                if flow.step < const.FLOW_STEP_4 and exists:
                    flow.step = const.FLOW_STEP_7
                    flow.save()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_roles_allocate Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色修改
def api_workflow_roles_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        role_id = request.POST.get('id', None)
        name = request.POST.get("name", None)  # 角色名称
        role_type = request.POST.get("type", None)  # 角色类型
        minimum = request.POST.get("min", None)  # 最小人数
        maximum = request.POST.get("max", None)  # 最大人数
        category = request.POST.get("category", None)  # 类别
        image_id = request.POST.get("image_id", None)  # 形象文件

        # 参数验证
        if all([role_id, name, role_type, minimum, maximum, category]):
            role = FlowRole.objects.filter(pk=role_id).first()
            if role:
                role.name = name
                role.min = minimum
                role.max = maximum
                role.type = role_type
                role.category = category
                if image_id:
                    role.image_id = image_id
                role.save()
                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': role.id, 'name': role.name, 'type': role.type, 'min': role.min, 'max': role.max,
                }

                flow = Flow.objects.get(pk=role.flow_id)
                if flow.step < const.FLOW_STEP_3:
                    flow.step = const.FLOW_STEP_3
                    flow.save()
            else:
                resp = code.get_msg(code.FLOW_ROLE_NOT_EXIST)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_roles_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 角色删除，删除相关角色分配，动作设置，角色设置
def api_workflow_roles_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id")
        ids = request.POST.get("ids")  # 角色id列表

        id_list = json.loads(ids)
        exist = ProjectRole.objects.filter(flow_role_id__in=id_list).exists()
        if exist:
            resp = code.get_msg(code.FLOW_ROLE_HAS_USE)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        FlowRoleAllocation.objects.filter(flow_id=flow_id, role_id__in=id_list).delete()
        FlowRoleActionNew.objects.filter(flow_id=flow_id, role_id__in=id_list).delete()
        ProcessRoleActionNew.objects.filter(flow_id=flow_id, role_id__in=id_list).update(del_flag=1)
        FlowRolePosition.objects.filter(flow_id=flow_id, role_id__in=id_list).delete()
        FlowRole.objects.filter(id__in=id_list).delete()

        exists = FlowRole.objects.filter(flow_id=flow_id).exists()
        flow = Flow.objects.get(pk=flow_id)
        if not exists:
            flow.step = const.FLOW_STEP_2
            flow.save()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'step': flow.step}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程素材批量修改
def api_workflow_docs_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        docs = request.POST.get("docs")  # 素材数据
        doc_list = json.loads(docs)

        # 验证操作指南
        if len(doc_list) == 0:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        opt_list = []
        for doc in doc_list:
            if doc['usage'] == 1:
                opt_list.append(doc)

        if len(opt_list) > 0:
            first = opt_list[0]
            for doc in opt_list:
                if doc['id'] != first['id']:
                    for node_id in first['node_ids']:
                        if node_id in doc['node_ids']:
                            resp = code.get_msg(code.FLOW_OPT_DOC_ONLY_ONE)
                            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow_id = None
        with transaction.atomic():
            for doc in doc_list:
                obj = FlowDocs.objects.get(pk=doc['id'])
                obj.usage = doc['usage']
                obj.type = doc['type']
                obj.save()
                flow_id = obj.flow_id
                FlowNodeDocs.objects.filter(flow_id=obj.flow_id, doc_id=doc['id']).update(del_flag=1)
                for node_id in doc['node_ids']:
                    FlowNodeDocs.objects.update_or_create(flow_id=obj.flow_id, node_id=node_id, doc_id=obj.id,
                                                          defaults={'del_flag': 0})
            flow = Flow.objects.get(pk=flow_id)
            if flow.step < const.FLOW_STEP_2:
                flow.step = const.FLOW_STEP_2
                flow.save()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'step': flow.step}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_docs_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程删除素材
def api_workflow_docs_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        doc_id = request.POST.get("doc_id", None)  # 素材ID

        doc = FlowDocs.objects.filter(id=doc_id).first()

        # 判断素材是否存在
        if doc:
            with transaction.atomic():
                doc.delete()
                FlowNodeDocs.objects.filter(flow_id=doc.flow_id, doc_id=doc_id).delete()
                exists = FlowNodeDocs.objects.filter(flow_id=doc.flow_id, del_flag=0).exists()
                flow = Flow.objects.get(pk=doc.flow_id)
                # todo 删除项目中的配置
                # if flow.step < const.FLOW_STEP_2:
                #     flow.step = const.FLOW_STEP_2
                #     flow.save()
                if exists is False:
                    flow.step = const.FLOW_STEP_1
                    flow.save()

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.FLOW_DOC_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_docs_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 添加角色
def api_workflow_roles_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 流程ID
        name = request.POST.get("name", None)  # 角色名称
        role_type = request.POST.get("type", None)  # 角色类型
        minimum = request.POST.get("min", None)  # 最小人数
        maximum = request.POST.get("max", None)  # 最大人数
        category = request.POST.get("category", None)  # 类别
        image_id = request.POST.get("image_id", None)  # 形象

        # 参数验证
        if all([flow_id, name, role_type, minimum, maximum, category, image_id]):
            flow = Flow.objects.get(pk=flow_id)
            role = FlowRole.objects.create(name=name, flow_id=flow_id, type=role_type, min=minimum, max=maximum,
                                           image_id=image_id, category=category)
            obj = RoleImage.objects.get(pk=role.image_id)
            img = {'id': obj.id, 'name': obj.name, 'file': obj.avatar.url if obj.avatar else None}
            if flow.step < const.FLOW_STEP_3:
                flow.step = const.FLOW_STEP_3
                flow.save()
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': role.id, 'name': role.name, 'type': role.type, 'min': role.min, 'max': role.max,
                'category': role.category, 'image': img, 'step': flow.step
            }
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_roles_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程上传素材
def api_workflow_docs_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 环节ID
        upload_file = request.FILES.get("file", None)  # 文件

        if flow_id is None or upload_file is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if len(upload_file.name) > 60:
            resp = code.get_msg(code.UPLOAD_FILE_NAME_TOOLONG_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id).first()
        if flow is None:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 获取文件类型，若为word文档则读取其内容保存到content
        content = ''
        file_type = tools.check_file_type(upload_file.name)
        if file_type == 1:
            full_text = []
            document = Document(upload_file)
            for para in document.paragraphs:
                full_text.append(para.text)

            content = '\n'.join(full_text)

        if flow.step < const.FLOW_STEP_2:
            flow.step = const.FLOW_STEP_2
            flow.save()

        doc = FlowDocs.objects.create(flow_id=flow_id, file=upload_file, name=upload_file.name, content=content,
                                      file_type=file_type)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'id': doc.id, 'name': doc.name, 'file': doc.file.url, 'flow_id': doc.flow_id, 'usage': doc.usage,
            'file_type': file_type, 'step': flow.step
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_docs_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        resp['m'] = u'请检查上传的文件是否正确'
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 环节设置
def api_workflow_nodes_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 流程ID
        nodes = request.POST.get("nodes", None)  # 环节

        flow = Flow.objects.filter(pk=flow_id).first()
        if flow is None:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if nodes:
            node_list = json.loads(nodes)
            end_node_id = get_end_node(flow_id)
            for node in node_list:
                if end_node_id == node['id']:
                    if node['type'] != const.PROCESS_EXPERIENCE_TYPE:
                        resp = code.get_msg(code.FLOW_END_NODE_MUST_REPORT_TYPE)
                        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            with transaction.atomic():
                for node in node_list:
                    obj = FlowNode.objects.get(pk=node['id'], flow_id=flow_id)
                    obj.name = node['name']
                    obj.condition = node['condition']
                    obj.look_on = node['look_on']
                    if obj.process_id and obj.process_id != node['process_id']:
                        # 场景变动，清除原配置
                        ProcessRoleActionNew.objects.filter(flow=flow, node_id=node['id']).update(actions='[]')
                        FlowRolePosition.objects.filter(flow_id=flow.pk, node_id=node['id']).update(del_flag=1)
                    obj.process_id = node['process_id']
                    obj.save()
                if flow.step < const.FLOW_STEP_1:
                    flow.step = const.FLOW_STEP_1
                    flow.save()
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'step': flow.step}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_nodes_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 程序模块列表
def api_workflow_processes(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get('search', None)

        qs = FlowProcess.objects.filter(del_flag=0)
        if search:
            qs = qs.filter(Q(name__icontains=search))

        process_list = []
        for process in qs:
            process_list.append({
                'name': process.name, 'type': process.type, 'id': process.id,
                'image': process.image.url if process.image else None
            })
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = process_list
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_processes Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程详情
def api_workflow_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get('flow_id', None)
        # 参数验证
        if flow_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        instance = Flow.objects.filter(pk=flow_id).first()
        if instance:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': instance.id, 'name': instance.name, 'xml': instance.xml,
                'animation1': file_info(instance.animation1),
                'animation2': file_info(instance.animation2), 'nodes': flow_nodes(instance.id),
                'created_by': user_simple_info(instance.created_by), 'step': instance.step,
                'create_time': instance.create_time.strftime('%Y-%m-%d')
            }
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 发布流程
def api_workflow_publish(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        ids = request.POST.get("ids", None)  # 流程ID列表

        if ids:
            id_list = json.loads(ids)
            with transaction.atomic():
                for pk in id_list:
                    flow = Flow.objects.filter(pk=pk).first()
                    # 判断流程是否存在和用户是否为流程的创建者, 而且已经画了流程图
                    # 判断流程是否已经发布
                    if flow and flow.created_by == request.user.id:
                        if flow.xml:
                            flow.status = 2
                            flow.save()
                        else:
                            resp = code.get_msg(code.FLOW_CHART_ERROR)
                            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                    else:
                        resp = code.get_msg(code.PERMISSION_DENIED)
                        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_publish Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询和流程相关的项目和实验
def api_workflow_related(request):
    resp = auth_check(request, 'GET')
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.GET.get('flow_id', None)
        if flow_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id).first()
        if flow:
            project_list = []
            projects = Project.objects.filter(flow_id=flow_id, del_flag=0)

            for pro in projects:
                experiments = Experiment.objects.filter(project_id=pro.id, del_flag=0)
                experiment_list = []
                for exp in experiments:
                    course_class = CourseClass.objects.filter(pk=exp.course_class_id).first()
                    if course_class and course_class.teacher1:
                        teacher_name = course_class.teacher1.name
                    else:
                        teacher_name = None
                    team = Team.objects.filter(pk=exp.team_id).first()
                    experiment_list.append({
                        'id': exp.id, 'name': u'{0} {1}'.format(exp.id, exp.name), 'teacher_name': teacher_name,
                        'team_id': exp.team_id, 'team_name': team.name if team else None, 'status': exp.status,
                        'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
                                                              course_class.term) if course_class else None
                    })
                project_list.append({
                    'experiments': experiment_list, 'id': pro.id, 'name': pro.name, 'level': pro.level,
                    'ability_tartget': pro.ability_target, 'exp_count': experiments.count(), 'type': pro.type
                })

            project_ids = Project.objects.filter(flow_id=flow_id).values_list('id', flat=True)
            jump_project_ids = ProjectJump.objects.filter(jump_project_id__in=project_ids).values_list('project_id',
                                                                                                       flat=True)
            projects = Project.objects.filter(pk__in=jump_project_ids, del_flag=0)

            for pro in projects:
                experiments = Experiment.objects.filter(project_id=pro.id, del_flag=0)
                experiment_list = []
                for exp in experiments:
                    course_class = CourseClass.objects.filter(pk=exp.course_class_id).first()
                    if course_class and course_class.teacher1:
                        teacher_name = course_class.teacher1.name
                    else:
                        teacher_name = None
                    team = Team.objects.filter(pk=exp.team_id).first()
                    experiment_list.append({
                        'id': exp.id, 'name': u'{0} {1}'.format(exp.id, exp.name), 'teacher_name': teacher_name,
                        'team_id': exp.team_id, 'team_name': team.name if team else None, 'status': exp.status,
                        'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
                                                              course_class.term) if course_class else None
                    })
                project_list.append({
                    'experiments': experiment_list, 'id': pro.id, 'name': pro.name, 'level': pro.level,
                    'ability_tartget': pro.ability_target, 'exp_count': experiments.count(), 'type': pro.type
                })

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = project_list
        else:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_related Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除流程
def api_workflow_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        # 参数验证
        if flow_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.get(pk=flow_id)
        if (flow.created_by != request.user.id and request.session['login_type']!=1):
            resp = code.get_msg(code.METHOD_NOT_ALLOW)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        with transaction.atomic():
            flow.del_flag = 1
            flow.save()
            # 删除关联环节、项目和实验等信息、包括跳转实验
            FlowNode.objects.filter(flow_id=flow_id).update(del_flag=1)
            FlowTrans.objects.filter(flow_id=flow_id).update(del_flag=1)
            project_ids = Project.objects.filter(flow_id=flow_id).values_list('id', flat=True)
            Project.objects.filter(flow_id=flow_id).update(del_flag=1)
            Experiment.objects.filter(project_id__in=project_ids).update(del_flag=1)

            jump_project_ids = ProjectJump.objects.filter(jump_project_id__in=project_ids).values_list('project_id',
                                                                                                       flat=True)
            Experiment.objects.filter(project_id__in=jump_project_ids).update(del_flag=1)
            ProjectJump.objects.filter(jump_project_id__in=project_ids).delete()
        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 修改流程
def api_workflow_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get('flow_id', None)
        name = request.POST.get('name', None)  # 名称
        animation1 = request.POST.get("animation1", None)  # 渲染动画1
        animation2 = request.POST.get("animation2", None)  # 渲染动画2
        type_label = int(request.POST.get("type_label", 1))  # 实验类型标签
        task_label = request.POST.get("task_label")  # 实验任务标签

        # 参数验证
        if flow_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id, created_by=request.user.id).first()
        if flow:
            # 验证流程名称是否唯一
            if Flow.objects.exclude(id=flow_id).filter(name=name, del_flag=0).exists():
                resp = code.get_msg(code.FLOW_SAME_NAME_HAS_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            with transaction.atomic():
                flow.name = name
                flow.type_label = type_label
                flow.task_label = task_label
                if animation1:
                    flow.animation1 = animation1
                if animation2:
                    flow.animation2 = animation2

                flow.save()
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': flow.id, 'name': flow.name, 'xml': flow.xml, 'animation1': file_info(flow.animation1),
                'animation2': file_info(flow.animation2), 'created_by': user_simple_info(flow.created_by),
                'create_time': flow.create_time.strftime('%Y-%m-%d')
            }
        else:
            resp = code.get_msg(code.METHOD_NOT_ALLOW)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 新建流程
def api_workflow_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        name = request.POST.get("name", None)  # 名称
        animation1 = request.POST.get("animation1", None)  # 渲染动画1
        animation2 = request.POST.get("animation2", None)  # 渲染动画2
        type_label = int(request.POST.get("type_label", 1))  # 实验类型标签
        task_label = request.POST.get("task_label", None)  # 试验任务标签

        # 参数验证
        if not all([name, animation1, animation2, type_label, task_label]):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证流程名称是否唯一
        if Flow.objects.filter(name=name, del_flag=0).exists():
            resp = code.get_msg(code.FLOW_SAME_NAME_HAS_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        instance = Flow.objects.create(name=name, animation1=animation1, animation2=animation2,
                                       task_label=task_label, type_label=type_label,
                                       created_by=request.user.id)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'id': instance.id, 'name': instance.name, 'xml': instance.xml, 'animation1': file_info(instance.animation1),
            'animation2': file_info(instance.animation2), 'created_by': user_simple_info(instance.created_by),
            'create_time': instance.create_time.strftime('%Y-%m-d')
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程列表
# todo 三期 - 加上是否共享字段 并且 只显示本单位数据
def api_workflow_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        status = request.GET.get("status", None)  # 流程状态（1未发布，2已发布， 默认全部）
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        user = request.user
        if request.session['login_type'] == 2:
            try:
                group = user.allgroups_set.all().first()  # get group that this user belongs to
                groupManagers = group.groupManagers.all()  # get all group managers
            except AttributeError as ae:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            createdBys = [groupManager.id for groupManager in groupManagers]
            companies = group.tcompany_set.all()  # get all companies
            for company in companies:
                companyManagers = company.tcompanymanagers_set.all()  # get all company managers
                for companyManager in companyManagers:
                    createdBys.append(companyManager.tuser.id)
            qs = Flow.objects.filter(
                Q(created_by=request.user.id, del_flag=0) | Q(status=2, is_public=1, created_by__in=createdBys,
                                                              del_flag=0)
                | Q(status=2, is_share=1, del_flag=0))
        elif request.session['login_type'] == 3:
            try:
                company = user.tcompanymanagers_set.all().first().tcompany  # get company info
                companyId = company.id  # company ID
                group = company.group  # get group info
            except AttributeError as ae:
                resp = code.get_msg(code.PERMISSION_DENIED)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            groupManagers = group.groupManagers.all()  # get all group managers
            groupMembers = [groupManager.id for groupManager in groupManagers]
            companies = group.tcompany_set.all()  # get all companies
            for company in companies:
                companyManagers = company.tcompanymanagers_set.all()  # get all company managers
                for companyManager in companyManagers:
                    groupMembers.append(companyManager.tuser.id)
                if company.id == companyId:
                    createdBys = [companyManager.tuser.id for companyManager in companyManagers]
            qs = Flow.objects.filter(
                Q(created_by=request.user.id, del_flag=0) | Q(status=2, is_public=1, created_by__in=createdBys,
                                                              del_flag=0)
                | Q(status=2, is_share=1, created_by__in=groupMembers, del_flag=0))
        elif request.session['login_type'] == 1:
            qs = Flow.objects.filter(Q(status=2, del_flag=0))
        else:
            # 只返回本人未发布和所有已发布, 三期， 加上共享数据
            # qs = Flow.objects.filter(Q(status=1, created_by=request.user.id, del_flag=0) | Q(status=2, del_flag=0)
            #                          | Q(is_share=1, del_flag=0))
            # # 三期 - 加上是否共享字段 并且 只显示本单位数据或者共享数据
            # if request.session['login_type'] != 4:
            #     users = Tuser.objects.filter(del_flag=0, manage=True, tcompany_id=user.tcompany_id)
            #     ids = [item.id for item in users]
            #     qs = qs.filter(Q(is_share=1) | Q(created_by__in=ids))
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 发布状态过滤
        if status:
            qs = qs.filter(status=int(status))

        # 搜索关键字过滤
        if search:
            qs = qs.filter(Q(name__icontains=search))

        # 分页
        paginator = Paginator(qs, size)

        try:
            flows = paginator.page(page)
        except EmptyPage:
            flows = paginator.page(1)

        results = []
        for flow in flows:
            user_info = user_simple_info(flow.created_by)
            if user_info is None:
                user_info = {}
            results.append({
                'id': flow.id, 'name': flow.name, 'xml': flow.xml, 'animation1': file_info(flow.animation1),
                'animation2': file_info(flow.animation2), 'status': flow.status, 'type_label': flow.type_label,
                'task_label': flow.task_label,
                'create_time': flow.create_time is not None and flow.create_time.strftime('%Y-%m-%d') or "",
                'step': flow.step, 'created_by': user_info, 'protected': flow.protected, 'is_share': flow.is_share,
                'is_public': flow.is_public
            })
        # 分页信息
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
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 环节走向条件查询 todo 添加跳转判断
def api_workflow_trans_query(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        project_id = request.GET.get('project_id', None)  # 实验ID
        flow_id = request.GET.get('flow_id', None)  # 流程id
        node_id = request.GET.get('node_id', None)  # 环节id
        direction = request.GET.get('direction', None)  # 流程走向

        # 参数验证
        if not all([flow_id, node_id, direction]):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # 验证流程是否存在
        flow = Flow.objects.filter(pk=flow_id).first()
        if flow is None:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id, flow_id=flow_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if direction not in [const.FLOW_FORWARD, const.FLOW_BACK]:
            resp = code.get_msg(code.FLOW_DIRECTION_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # 根据走向查询分支条件
        tran_list = []
        # 前进
        if direction == const.FLOW_FORWARD:
            trans = FlowTrans.objects.filter(flow_id=flow_id, incoming=node.task_id, del_flag=0)
            next_nodes = []
            for item in trans:
                # 判断是否有gateway类型的分支
                if item.outgoing.startswith('ExclusiveGateway'):
                    gateway_trans = FlowTrans.objects.filter(flow_id=flow_id, incoming=item.outgoing, del_flag=0)
                    for gateway_tran in gateway_trans:
                        obj = FlowNode.objects.filter(flow_id=flow_id, task_id=gateway_tran.outgoing,
                                                      del_flag=0).first()
                        if obj:
                            next_nodes.append({'tran_id': gateway_tran.id, 'tran_name': gateway_tran.name, 'node': obj})
                else:
                    obj = FlowNode.objects.filter(task_id=item.outgoing, flow_id=flow_id, del_flag=0).first()
                    if obj:
                        next_nodes.append({'tran_id': item.id, 'tran_name': item.name, 'node': obj})

            for item in next_nodes:
                process_type = item['node'].process.type
                jump_project_id = None
                # 如果下一环节为跳转，重新获取跳转项目id和项目流程的第一个节点tran_id
                if process_type == const.PROCESS_JUMP_TYPE:
                    jump = ProjectJump.objects.filter(project_id=project_id, node_id=item['node'].pk).first()
                    if jump:
                        jump_project_id = jump.jump_project_id
                    else:
                        continue

                tran_list.append({
                    'id': item['tran_id'], 'name': item['tran_name'], 'process_type': process_type,
                    'jump_project_id': jump_project_id,
                    # condition': item['tran_name'] if item['tran_name']
                    # else u'走向'.join([node.name, item['node'].name])
                    'condition': u'走向'.join([node.name, item['node'].name])
                })
        else:
            trans = FlowTrans.objects.filter(flow_id=flow_id, outgoing=node.task_id, del_flag=0)
            previous_nodes = []
            for item in trans:
                # 判断是否有gateway类型的分支
                if item.incoming.startswith('ExclusiveGateway'):
                    gateway_trans = FlowTrans.objects.filter(flow_id=flow_id, outgoing=item.incoming, del_flag=0)
                    for gateway_tran in gateway_trans:
                        obj = FlowNode.objects.filter(flow_id=flow_id, task_id=gateway_tran.incoming,
                                                      del_flag=0).first()
                        if obj:
                            previous_nodes.append({
                                'tran_id': gateway_tran.id, 'tran_name': gateway_tran.name,
                                'node': obj
                            })
                else:
                    obj = FlowNode.objects.filter(task_id=item.incoming, flow_id=flow_id, del_flag=0).first()
                    if obj:
                        previous_nodes.append({
                            'tran_id': item.id, 'tran_name': item.name,
                            'node': obj
                        })
            for item in previous_nodes:
                tran_list.append({
                    'id': item['tran_id'], 'name': item['tran_name'], 'process_type': item['node'].process.type,
                    'condition': u'走向'.join([node.name, item['node'].name])
                })
        if node.condition:
            for item in node.condition.split('|'):
                item = item.strip()
                if item != '':
                    tran_list.append({
                        'id': None, 'name': item, 'condition': item, 'process_type': 0,
                    })

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = tran_list
    except Exception as e:
        logger.exception('api_workflow_trans_query Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_style(height, bold=False):
    style = xlwt.XFStyle()  # 初始化样式
    font = xlwt.Font()  # 为样式创建字体
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


# 操作指南模板
def workflow_opt_export(request):
    flow_id = request.GET.get('flow_id', None)
    try:
        instance = Flow.objects.filter(pk=flow_id).first()
        if instance:
            nodes = flow_nodes(instance.id)
            report = xlwt.Workbook(encoding='utf8')
            sheet = report.add_sheet(u'操作指南模板')
            title = [u'编号', u'环节名称', u'素材名称', u'素材类型', u'操作指南']
            for i in range(0, len(title)):
                sheet.write(0, i, title[i], set_style(220, True))
            row = 1

            for r in nodes:
                sheet.write(row, 0, r['id'])
                sheet.write(row, 1, r['name'])
                row += 1

            response = HttpResponse(content_type='application/vnd.ms-excel')
            filename = urlquote(u'%s操作指南导入模板' % instance.name)
            response['Content-Disposition'] = u'attachment;filename=%s.xls' % filename
            report.save(response)
            return response
        else:
            return redirect('/404/')
    except Exception as e:
        logger.exception('workflow_node_export Exception:{0}'.format(str(e)))
        return redirect('/500/')


# 流程上传素材
def api_workflow_opt_import(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 环节ID
        upload_file = request.FILES.get("file", None)  # 文件

        if flow_id is None or upload_file is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        flow = Flow.objects.filter(pk=flow_id).first()
        if flow is None:
            resp = code.get_msg(code.FLOW_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 解析exl内容，生成docx文件，保存数据库。
        wb = xlrd.open_workbook(filename=None, file_contents=upload_file.read())
        sheet = wb.sheet_by_index(0)
        logger.info('name:%s,rows:%s,cols:%s' % (sheet.name, sheet.nrows, sheet.ncols))
        has_import = False

        # 三期重复上传覆盖原来的操作指南， 那么上传之前先删一遍
        docs = FlowDocs.objects.filter(flow_id=flow_id, usage=1)
        if docs:
            docs.delete()

        for i in range(1, sheet.nrows):
            node_id = sheet.cell(i, 0).value
            node_name = sheet.cell(i, 1).value
            doc_name = sheet.cell(i, 2).value
            doc_type = sheet.cell(i, 3).value
            content = sheet.cell(i, 4).value
            logger.info('node_id:%s,node_name:%s,doc_name:%s,doc_type:%s,content:%s' % (int(node_id), node_name,
                                                                                        doc_name, doc_type, content))
            if None in (doc_name, content) or '' in (doc_name, content):
                continue
            node_id = int(node_id)
            if FlowNode.objects.filter(pk=node_id, del_flag=0).exists():
                doc_name = '%s.docx' % doc_name
                path = flow_doc_save(flow_id, doc_name, content)

                doc = FlowDocs.objects.filter(flow_id=flow_id, name=doc_name, usage=1).first()
                if doc:
                    FlowDocs.objects.filter(flow_id=flow_id, name=doc_name, usage=1).update(content=content,
                                                                                            file=path,
                                                                                            type=doc_type)
                else:
                    doc = FlowDocs.objects.create(flow_id=flow_id, name=doc_name, content=content, usage=1,
                                                  type=doc_type, file_type=1, file=path)

                FlowNodeDocs.objects.update_or_create(flow_id=flow_id, node_id=node_id, doc_id=doc.id,
                                                      defaults={'del_flag': 0})
                has_import = True

        if has_import and flow.step < const.FLOW_STEP_2:
            flow.step = const.FLOW_STEP_2
            flow.save()

        if not has_import:
            resp = code.get_msg(code.FLOW_OPT_DOC_IMPORT_FAIL)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_opt_import Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.EXPERIMENT_FILE_TYPE_NOT_ALLOW)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程设置保护/解除保护
def api_workflow_protected(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if request.session['login_type']!=1:
        resp = code.get_msg(code.METHOD_NOT_ALLOW)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        flow_id = request.POST.get("flow_id", None)  # 环节ID

        flow = Flow.objects.get(pk=flow_id)

        # 环节保护状态取反
        if flow.protected == 1:
            flow.protected = 0
        else:
            flow.protected = 1

        flow.save()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_workflow_opt_import Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期 - 共享
def api_workflow_share(request):
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
        Flow.objects.filter(id__in=ids, created_by=request.user.id).update(is_share=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_share Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_workflow_unshare(request):
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
        Flow.objects.filter(id__in=ids, created_by=request.user.id).update(is_share=0)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_unshare Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_workflow_public(request):
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
        Flow.objects.filter(id__in=ids, created_by=request.user.id).update(is_public=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_public Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def api_workflow_unpublic(request):
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
        Flow.objects.filter(id__in=ids, created_by=request.user.id).update(is_public=0)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_public Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")