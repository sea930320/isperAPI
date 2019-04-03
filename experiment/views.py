#!/usr/bin/python
# -*- coding=utf-8 -*-
import json
import logging

from account.models import Tuser
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponse
from experiment.models import *
from experiment.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation
from workflow.service import get_start_node, bpmn_color
from datetime import datetime

logger = logging.getLogger(__name__)


# 用户编辑模板
def api_experiment_template_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    experiment_id = request.POST.get('experiment_id', None)  # 实验id
    node_id = request.POST.get('node_id', None)  # 环节id
    doc_id = request.POST.get('doc_id', None)  # 模板素材id
    content = request.POST.get('content', '')  # 内容

    if None in (experiment_id, node_id, doc_id):
        resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            doc = ExperimentDocContent.objects.filter(pk=doc_id).first()
            path = experiment_template_save(experiment_id, node_id, doc.name, content)
            ExperimentDocContent.objects.filter(pk=doc_id).update(content=content, created_by=request.user.id,
                                                                  file=path, has_edited=True)

            clear_cache(exp.pk)
            resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_template_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户编辑模板
def api_experiment_template_new(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get('experiment_id', None)  # 实验id
        node_id = request.POST.get('node_id', None)  # 环节id
        name = request.POST.get('name', '')  # 内容
        content = request.POST.get('content', '')  # 内容
        role_id = request.POST.get('role_id', None)

        if None in (experiment_id, node_id, name):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            name = '%s.docx' % name
            path = experiment_template_save(experiment_id, node_id, name, content)
            ExperimentDocContent.objects.create(experiment_id=experiment_id, node_id=node_id, role_id=role_id,
                                                content=content, name=name, created_by=request.user.id,
                                                file_type=1, file=path, has_edited=True)

            clear_cache(exp.pk)
            resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_template_new Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 用户编辑模板签名
def api_experiment_template_sign(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    experiment_id = request.POST.get('experiment_id', None)  # 实验id
    node_id = request.POST.get('node_id', None)  # 环节id
    role_id = request.POST.get('role_id', None)
    doc_id = request.POST.get('doc_id', None)  # 模板素材id
    status = request.POST.get('status', None)
    logger.info('experiment_id:%s,node_id:%s,role_id:%s,doc_id:%s,status:%s' % (experiment_id, node_id,
                                                                                role_id, doc_id, status))
    if None in (experiment_id, node_id, doc_id, role_id):
        resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        role = ProjectRole.objects.filter(pk=role_id).first()
        if role is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            sign = '{0}({1})'.format(request.user.name, role.name)
            if status == '1':
                ExperimentDocContent.objects.filter(pk=doc_id, experiment_id=experiment_id,
                                                    node_id=node_id).update(sign_status=1, sign=sign, has_edited=True)
            else:
                ExperimentDocContent.objects.filter(pk=doc_id, experiment_id=experiment_id,
                                                    node_id=node_id).update(sign_status=0, sign='', has_edited=True)

            doc_sign = ExperimentDocContent.objects.filter(pk=doc_id).first()
            if doc_sign is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'sign_status': doc_sign.sign_status, 'sign': doc_sign.sign}

            clear_cache(exp.pk)
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_template_sign Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验所属项目素材查询
def api_experiment_templates(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        role_id = request.GET.get('role_id', None)
        usage = request.GET.get("usage", None)  # 用途
        logger.info('experiment_id:%s,node_id:%s,role_id:%s,usage:%s' % (experiment_id, node_id, role_id, usage))

        if None in (experiment_id, node_id):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            user_id = request.user.pk
            if usage and usage == '3':
                if role_id is None:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 复制编辑模板
                doc_ids = ProjectDocRole.objects.filter(project_id=exp.cur_project_id, node_id=node_id,
                                                        role_id=role_id).values_list('doc_id', flat=True)
                project_docs = ProjectDoc.objects.filter(pk__in=doc_ids, usage=3)
                for doc in project_docs:
                    is_exists = ExperimentDocContent.objects.filter(experiment_id=exp.pk, node_id=node_id,
                                                                    doc_id=doc.pk, role_id=role_id).exists()
                    if not is_exists:
                        path = experiment_template_save(exp.pk, node_id, doc.name, doc.content)
                        ExperimentDocContent.objects.create(experiment_id=exp.pk, node_id=node_id, doc_id=doc.pk,
                                                            role_id=role_id, name=doc.name, content=doc.content,
                                                            created_by=user_id, file_type=1, file=path)

            doc_list = get_experiment_templates(exp, node_id, role_id, usage)
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = doc_list
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_templates Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验编辑应用模板详情
def api_experiment_templates_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        doc_id = request.GET.get('doc_id', None)

        if experiment_id:
            exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
            if exp:
                doc = ExperimentDocContent.objects.filter(pk=doc_id, experiment_id=experiment_id,
                                                          node_id=node_id).first()
                if doc:
                    data = {
                        'id': doc.pk, 'name': doc.name, 'file_type': doc.file_type,
                        'sign': doc.sign, 'sign_status': doc.sign_status, 'content': doc.content
                    }
                    resp = code.get_msg(code.SUCCESS)
                    resp['d'] = data
                else:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            else:
                resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_templates_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验文件展示列表
def api_experiment_file_display_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        path_id = request.GET.get("path_id", None)  # 环节id

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            doc_list = get_experiment_display_files(exp, node_id, path_id)
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
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_file_display_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验文件详情
def api_experiment_doc_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get('node_id', None)
        doc_id = request.GET.get('doc_id', None)

        if experiment_id:
            exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
            if exp:
                doc = ExperimentDocContent.objects.filter(pk=doc_id, experiment_id=exp.pk,
                                                          node_id=node_id, has_edited=True).first()
                if doc:
                    data = {
                        'id': doc.doc_id, 'filename': doc.name, 'content': doc.content, 'file_type': doc.file_type,
                        'signs': [{'sign_status': doc.sign_status, 'sign': doc.sign}],
                        'url': doc.file.url if doc.file else None
                    }
                else:
                    # 提交的文件
                    doc = ExperimentDoc.objects.filter(pk=doc_id, experiment_id=exp.pk, node_id=node_id).first()
                    if doc is None:
                        resp = code.get_msg(code.PARAMETER_ERROR)
                        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                    sign_list = ExperimentDocSign.objects.filter(doc_id=doc.pk).values('sign', 'sign_status')
                    data = {
                        'id': doc.id, 'filename': doc.filename, 'content': doc.content, 'file_type': doc.file_type,
                        'signs': list(sign_list), 'url': doc.file.url if doc.file else None
                    }

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = data
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            else:
                resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_sign_doc_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 保存实验心得
def api_experiment_save_experience(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get('experiment_id', None)  # 实验id
        content = request.POST.get('content', '')
        if experiment_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if exp.status == 2:
            if content is None or len(content) > 30000:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            instance, flag = ExperimentExperience.objects.update_or_create(experiment_id=experiment_id,
                                                                           created_by=request.user.id,
                                                                           defaults={'content': content,
                                                                                     'created_by': request.user.id})
            data = {
                'id': instance.pk, 'content': instance.content, 'status': instance.status,
                'created_by': user_simple_info(instance.created_by),
                'create_time': instance.create_time.strftime('%Y-%m-%d')
            }
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        elif exp.status == 1:
            resp = code.get_msg(code.EXPERIMENT_HAS_NOT_STARTED)
        else:
            resp = code.get_msg(code.EXPERIMENT_HAS_FINISHED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_display_application Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节详情
def api_experiment_node_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", None)  # 角色id

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=exp.cur_project_id)

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 获取上个环节
        pre_node = get_pre_node_path(exp)
        pre_node_id = None
        if pre_node:
            pre_node_id = pre_node.node_id

        # 路径
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

        user_id = request.user.id
        # 判断该实验环节是否存在该角色
        if role_id is None:
            role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                              path_id=path.pk, user_id=user_id).first()
            if role_status is None:
                resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 当前用户可选角色
        role_list_temp = get_roles_status_by_user(exp, path, user_id)

        role_list = []

        # 三期 老师以实验指导登录进来，老师只观察只给一个观察者的角色;老师以实验者登录进来，要去掉老师的观察者角色
        if request.session['login_type'] == 2:
            for role_temp in role_list_temp:
                if role_temp['name'] == const.ROLE_TYPE_OBSERVER:
                    role_list.append(role_temp)
        else:
            for role_temp in role_list_temp:
                if role_temp['name'] != const.ROLE_TYPE_OBSERVER:
                    role_list.append(role_temp)

        # 当前环节所有角色状态
        role_status_list_temp = get_all_simple_roles_status(exp, node, path)

        role_status_list = []
        # 三期 老师以实验指导登录进来, 不显示老师角色
        # 这
        for role_temp in role_status_list_temp:
            if role_temp['role_name'] != const.ROLE_TYPE_OBSERVER:
                role_status_list.append(role_temp)

        # 是否投票
        has_vote = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                       path_id=path.pk, role_id=role_id, vote_status=0).exists()
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
        team = Team.objects.filter(pk=exp.team_id).first()
        can_opt = True if exp.created_by == request.user.id or team.leader == request.user.id else False

        # 实验心得
        experience = ExperimentExperience.objects.filter(experiment_id=exp.id, created_by=request.user.pk).first()
        experience_data = {'status': 1, 'content': ''}
        if experience:
            experience_data = {
                'id': experience.id, 'content': experience.content, 'status': experience.status,
                'created_by': user_simple_info(experience.created_by),
                'create_time': experience.create_time.strftime('%Y-%m-%d')
            }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'roles': role_list, 'process': process, 'process_actions': process_action_list, 'can_opt': can_opt,
            'role_status': role_status_list, 'id': exp.id, 'name': exp.name, 'experience': experience_data,
            'node': {'id': node.id, 'name': node.name, 'condition': node.condition}, 'pre_node_id': pre_node_id,
            'huanxin_id': exp.huanxin_id, 'control_status': path.control_status, 'entire_graph': project.entire_graph,
            'leader': team.leader if team else None, 'flow_id': project.flow_id,
            'has_vote': False if has_vote else True, 'end_vote': end_vote
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节角色素材
def api_experiment_node_role_docs(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", None)  # 角色id

        user = request.user

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=exp.cur_project_id)

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        # 判断该实验环节是否存在该角色
        if role_id is None:
            role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                              path_id=path.pk, user_id=request.user.id).first()
            # 三期 组长没有权限也可以执行一些操作
            # 当前环节不存在该角色 除了组长
            team = Team.objects.filter(id=exp.team_id).first()
            if role_status is None and user.id != team.leader:
                resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            if role_status is not None:
                role_id = role_status.role_id

        # 获取该环节角色项目所有素材
        docs = get_node_role_docs(exp, node_id, project.pk, project.flow_id, role_id)

        # 前面所有环节素材
        pre_doc_list = get_pre_node_role_docs(exp, node_id, project.pk, role_id)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'operation_guides': docs['operation_guides'],
            'project_tips_list': docs['project_tips_list'],
            'cur_doc_list': docs['cur_doc_list'],
            'pre_doc_list': pre_doc_list,
            'id': exp.id, 'name': exp.name,
            'flow_id': project.flow_id
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_role_docs Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验功能按钮
def api_experiment_node_function(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", None)  # 角色id
        logger.info('experiment_id:%s, node_id:%s, role_id:%s' % (experiment_id, node_id, role_id))

        user_id = request.user.id
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.filter(pk=exp.cur_project_id).first()
        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        # 判断该实验环节是否存在该角色
        if role_id is None:
            role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                              path_id=path.pk, user_id=user_id).first()
            if role_status is None:
                resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            else:
                role_id = role_status.role_id

        role_status = ExperimentRoleStatus.objects.filter(experiment_id=exp.id, node_id=node_id,
                                                          path_id=path.pk, role_id=role_id).first()
        if role_status is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 三期 - 根据上一步骤自动入席 判断是否入席
        eps = ExperimentPositionStatus.objects.filter(experiment_id=exp.id, node_id=path.node_id, path_id=path.id,
                                                      role_id=role_id)
        if eps:
            experiment_position_status = eps.first()
            if experiment_position_status.sitting_status == 2:  # 已入席
                role_status.sitting_status = const.SITTING_DOWN_STATUS

        # 用户角色状态
        # 当前用户可选角色
        role_list = get_roles_status_simple_by_user(exp, node, path, user_id)

        # 功能动作列表根据环节和角色分配过滤
        role = ProjectRole.objects.filter(pk=role_id).first()
        flow_action_ids = []
        process_action_ids = []
        if role:
            flow_actions = FlowRoleActionNew.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                            role_id=role.flow_role_id, del_flag=0).first()

            process_actions = ProcessRoleActionNew.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                  role_id=role.flow_role_id, del_flag=0).first()
            if process_actions and process_actions.actions:
                process_action_ids = json.loads(process_actions.actions)
            if flow_actions and flow_actions.actions:
                flow_action_ids = json.loads(flow_actions.actions)

        # 当前角色动画
        process_action_list = get_role_process_actions(exp, path, role_id, process_action_ids)

        # 功能按钮
        # 是否有结束环节的权限
        # role_conf = ProjectRoleAllocation.objects.filter(project_id=exp.cur_project_id, node_id=node_id,
        #                                                  role_id=role_id).first()
        if ProjectRoleAllocation.objects.filter(project_id=exp.cur_project_id, node_id=node_id,
                                                role_id=role_id, can_terminate=True).exists():
            can_terminate = True
        else:
            can_terminate = False
        # can_brought = False
        # if role_conf:
        #     if role_conf.can_terminate:
        #         can_terminate = True
            # if role_conf.can_brought:
            #     can_brought = True
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
                    if role_status:
                        if item.cmd == const.ACTION_DOC_SHOW:
                            if role_status.show_status != 1:
                                disable = True
                        if item.cmd == const.ACTION_DOC_SUBMIT:
                            if role_status.submit_status != 1:
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
            if role_status.sitting_status == const.SITTING_UP_STATUS:
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
                    report_exists = ExperimentReportStatus.objects.filter(experiment_id=exp.pk, node_id=node_id,
                                                                          path_id=path.pk, role_id=role.pk,
                                                                          schedule_status=const.SCHEDULE_UP_STATUS).exists()
                    if report_exists:
                        disable = True

                # 起立坐下互斥
                if item.cmd == const.ACTION_ROLE_STAND:
                    if role_status.stand_status == 1:
                        disable = True

                if item.cmd == const.ACTION_ROLE_SITDOWN:
                    if role_status.stand_status == 2:
                        disable = True
                # 约见
                if item.cmd == const.ACTION_ROLE_MEET:
                    disable = True

            # 判断报告按钮状态
            if item.cmd == const.ACTION_ROLE_TOWARD_REPORT:
                disable = True
                report_exists = ExperimentReportStatus.objects.filter(experiment_id=exp.pk, node_id=node_id,
                                                                      path_id=path.pk, role_id=role.pk,
                                                                      schedule_status=const.SCHEDULE_OK_STATUS).exists()
                if report_exists:
                    disable = False

            if item.cmd == const.ACTION_ROLE_EDN_REPORT:
                disable = True
                report_exists = ExperimentReportStatus.objects.filter(experiment_id=exp.pk, node_id=node_id,
                                                                      path_id=path.pk, role_id=role.pk,
                                                                      schedule_status=const.SCHEDULE_UP_STATUS).exists()
                if report_exists:
                    disable = False

            btn = {
                'id': item.id, 'name': item.name, 'cmd': item.cmd, 'disable': disable
            }
            function_action_list.append(btn)

        resp = code.get_msg(code.SUCCESS)

        # 三期，如果进来的是老师观察者角色， 没有任何功能按钮， tmd
        if role.type == const.ROLE_TYPE_OBSERVER:
            function_action_list = []
            process_action_list = []

        resp['d'] = {'function_action_list': function_action_list,
                     'process_action_list': process_action_list,
                     'user_roles': role_list}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_node_function Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 待请出角色列表
def api_experiment_role_out_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", 0)  # 角色id

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp and exp.node_id == int(node_id):
            project = Project.objects.filter(pk=exp.cur_project_id).first()
            path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

            role_ids = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=exp.node_id,
                                                           path_id=path.pk,
                                                           sitting_status=2).exclude(come_status=9
                                                                                     ).values_list('role_id', flat=True)
            role_list = []
            for id in role_ids:
                if id == int(role_id):
                    continue
                role = ProjectRole.objects.get(pk=id)
                role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                role_id=role.flow_role_id, del_flag=0).first()
                if role_position:
                    pos = FlowPosition.objects.filter(pk=role_position.position_id).first()
                    if pos:
                        code_position = pos.code_position
                    else:
                        continue
                else:
                    continue
                role_list.append({
                    'id': role.id, 'name': role.name, 'code_position': code_position
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = role_list
        elif exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_role_out_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 待请入角色列表
def api_experiment_role_in_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", 0)  # 角色id

        exp = Experiment.objects.filter(pk=experiment_id).first()

        # 判断实验是否存在以及实验当前环节是否是node_id
        if exp and exp.node_id == int(node_id):
            project = Project.objects.filter(pk=exp.cur_project_id).first()
            path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

            role_ids = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=exp.node_id,
                                                           path_id=path.pk,
                                                           sitting_status=1).exclude(come_status=9
                                                                                     ).values_list('role_id', flat=True)
            role_list = []
            for id in role_ids:
                if id == int(role_id):
                    continue

                role = ProjectRole.objects.get(pk=id)
                role_position = FlowRolePosition.objects.filter(flow_id=project.flow_id, node_id=node_id,
                                                                role_id=role.flow_role_id, del_flag=0).first()
                if role_position:
                    pos_status = ExperimentPositionStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                                         path_id=path.pk,
                                                                         position_id=role_position.position_id).first()

                    if pos_status and pos_status.sitting_status == const.SITTING_DOWN_STATUS:
                        continue

                    pos = FlowPosition.objects.filter(pk=role_position.position_id).first()
                    if pos:
                        code_position = pos.code_position
                    else:
                        continue
                else:
                    continue
                role_list.append({
                    'id': role.id, 'name': role.name, 'code_position': code_position
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = role_list
        elif exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_role_in_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 个人笔记列表
def api_experiment_note_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            project = Project.objects.get(pk=exp.cur_project_id)
            nodes = FlowNode.objects.filter(flow_id=project.flow_id)

            note_list = []
            for item in nodes:
                note = ExperimentNotes.objects.filter(experiment_id=experiment_id, node_id=item.id,
                                                      created_by=request.user.id, del_flag=0).first()
                can_edit = True if exp.node_id == item.id else False
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
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_note_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 创建实验笔记
def api_experiment_note_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id")  # 实验id
        node_id = request.POST.get("node_id")  # 环节id
        content = request.POST.get("content")  # 内容

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            # 验证实验环节是否在该环节
            if exp.node_id == int(node_id):
                note, created = ExperimentNotes.objects.update_or_create(experiment_id=experiment_id, node_id=node_id,
                                                                         created_by=request.user.id,
                                                                         defaults={'content': content})

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': note.id, 'content': note.content, 'node_id': note.node_id,
                    'experiment_id': note.experiment_id,
                    'created_by': user_simple_info(note.created_by)
                }
            else:
                resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_note_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 个人笔记列表
def api_experiment_note_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id", None)  # 实验id
        node_id = request.GET.get("node_id")  # 实验id
        if None in (experiment_id, node_id):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            node = FlowNode.objects.filter(pk=node_id).first()
            if node is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            note = ExperimentNotes.objects.filter(experiment_id=experiment_id, node_id=node.id,
                                                  created_by=request.user.id, del_flag=0).first()
            if note:
                note_dict = {'id': note.id, 'content': note.content}
            else:
                note_dict = None

            data = {
                'node_id': node.id, 'node_name': node.name, 'note': note_dict
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_note_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验详情
def api_experiment_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验id
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            # if not exp.course_class_id:
            #     logger.exception('api_experiment_detail Exception:该实验没有注册到课堂')
            #     resp = code.get_msg(code.EXPERIMENT_NOT_REGISTER)
            #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            data = get_experiment_detail(exp)

            # 三期记录用户最后一次进入的实验id
            user = request.user
            user.last_experiment_id = experiment_id
            user.save()

            user_roles = []
            if exp.status == 1:
                control_status = 1
                path_id = None
            else:
                path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
                control_status = path.control_status
                path_id = path.pk
                # user_roles = get_roles_status_by_user(exp, path, request.user.pk)
                # 三期 - 老师进入实验观察学生做实验  ——ps：二手项目真是个麻烦事
                # 获取用户登录类型是老师的
                if request.session['login_type'] == 2:
                    # 老师没有角色就给他创建各种角色， mdzz~zzz， 老师观察者权限
                    p_temp = Project.objects.get(pk=exp.project_id)
                    f_role_temp = FlowRole.objects.filter(flow_id=p_temp.flow_id, name=const.ROLE_TYPE_OBSERVER,
                                                          type=const.ROLE_TYPE_OBSERVER)
                    if not f_role_temp:
                        f_role_temp = FlowRole.objects.create(flow_id=p_temp.flow_id, name=const.ROLE_TYPE_OBSERVER,
                                                              type=const.ROLE_TYPE_OBSERVER, category=99, image_id=40,
                                                              min=1, max=100)
                    else:
                        f_role_temp = f_role_temp.first()
                    p_role_temp = ProjectRole.objects.filter(project_id=exp.project_id, flow_role_id=f_role_temp.id,
                                                             name=const.ROLE_TYPE_OBSERVER,
                                                             type=const.ROLE_TYPE_OBSERVER,)
                    if not p_role_temp:
                        p_role_temp = ProjectRole.objects.create(project_id=exp.project_id, category=99,
                                                                 flow_role_id=f_role_temp.id, image_id=40,
                                                                 name=const.ROLE_TYPE_OBSERVER,
                                                                 type=const.ROLE_TYPE_OBSERVER,)
                    else:
                        p_role_temp = p_role_temp.first()
                    e_role_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=path.node_id,
                                                                      user_id=request.user.id, role_id=p_role_temp.id,
                                                                      path_id=path.pk)
                    if not e_role_temp:
                        e_role_temp = ExperimentRoleStatus.objects.create(experiment_id=experiment_id,
                                                                          node_id=path.node_id, user_id=request.user.id,
                                                                          role_id=p_role_temp.id, path_id=path.pk,
                                                                          sitting_status=const.SITTING_DOWN_STATUS)
                    else:  # 老师默认入席
                        e_role_temp.update(sitting_status=const.SITTING_DOWN_STATUS)
                    # 将老师注册到环信群组
                    easemob_members = []
                    easemob_members.append(request.user.id)
                    easemob_success, easemob_result = easemob.add_groups_member(exp.huanxin_id, easemob_members)
                    pass
                # 重新获取一遍user_roles
                user_roles_temp = get_roles_status_by_user(exp, path, request.user.pk)
                # user_roles = []
                # 三期 老师以实验指导登录进来，老师只观察只给一个观察者的角色;
                # 老师以实验者登录进来，要去掉老师的观察者角色
                if request.session['login_type'] == 2:
                    for role_temp in user_roles_temp:
                        if role_temp['name'] == const.ROLE_TYPE_OBSERVER:
                            user_roles.append(role_temp)
                else:
                    for role_temp in user_roles_temp:
                        if role_temp['name'] != const.ROLE_TYPE_OBSERVER:
                            user_roles.append(role_temp)

                # 取一个角色id
                mr = MemberRole.objects.filter(experiment_id=experiment_id, user_id=request.user.pk, del_flag=0).first()
                if mr:
                    data['without_node_user_role_id'] = mr.role_id
                # 获取角色相关环节
                data['with_user_nodes'] = get_user_with_node(exp, request.user.pk)

            data['control_status'] = control_status
            data['path_id'] = path_id
            data['user_roles'] = user_roles
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data

        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)

        # 三期 - 到达指定环节还有角色没有设置提示设置角色
        node = FlowNode.objects.filter(pk=exp.node_id, del_flag=0).first()
        if node:
            # 已设置的角色
            role_list_has = MemberRole.objects.filter(experiment_id=experiment_id, project_id=exp.project_id,
                                                      del_flag=0)
            role_id_list_has = [item.role_id for item in role_list_has]  # 项目角色id
            # 环节需要的角色
            project_role_need = ProjectRoleAllocation.objects.filter(project_id=exp.project_id, node_id=node.pk)
            role_id_list_need = [item.role_id for item in project_role_need]  # 流程角色id
            # 没有设置的角色名称
            role_name_not_set = []
            # 如果当前环节需要的角色还没有设置，则加入到role_name_not_set
            for role_id_need_temp in role_id_list_need:
                if role_id_need_temp not in role_id_list_has:
                    role_need_temp = ProjectRole.objects.filter(id=role_id_need_temp).first()
                    # 除掉老师观察者
                    if role_need_temp.name != const.ROLE_TYPE_OBSERVER:
                        role_name_not_set.append(role_need_temp.name)
            if len(role_name_not_set) > 0:
                logger.info('当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set))
                # resp['c'] = code.get_msg(code.EXPERIMENT_ROLE_NOT_SET)
                resp['m'] = '当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set)
                data['role_not_set'] = resp['m']
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 开始实验任务
def api_experiment_start(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id")  # 实验ID
        exp = Experiment.objects.filter(pk=experiment_id).first()
        logger.info('api_experiment_start:experiment_id=%s' % experiment_id)
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if exp.status != 1:
            resp = code.get_msg(code.EXPERIMENT_HAS_STARTED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # todo 三期 - 有角色未分配也可以开始
        # 在detail接口中提示当前环节的角色是否设置完
        # if not experiment_can_start(exp, exp.project_id):
        #     resp = code.get_msg(code.EXPERIMENT_ROLE_ALLOCATE_ERROR)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 项目开始
        project = Project.objects.get(pk=exp.project_id)
        # 验证项目中是否有未配置的跳转项目
        if not check_jump_project(project):
            resp = code.get_msg(code.EXPERIMENT_JUMP_PROJECT_SETUP_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        first_node_id = get_start_node(project.flow_id)
        team = Team.objects.filter(pk=exp.team_id).first()
        if not team:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 环信创建群聊
        ids = list(
            TeamMember.objects.filter(team_id=exp.team_id,
                                      del_flag=const.DELETE_FLAG_NO).values_list('user_id', flat=True))
        if not ids:
            resp = code.get_msg(code.TEAM_MEMBER_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 注册所有的群组用户到环信群组
        easemob_success, easemob_result = easemob.create_groups(str(exp.pk), str(request.user.pk), ids)
        logger.info(u'easemob create_groups:{}{}'.format(easemob_success, easemob_result))

        if easemob_success is False:
            resp = code.get_msg(code.EXPERIMENT_START_FAILED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        node = FlowNode.objects.get(pk=first_node_id)
        with transaction.atomic():
            # 实验路径
            path = ExperimentTransPath.objects.create(experiment_id=exp.pk, node_id=first_node_id,
                                                      project_id=exp.project_id, task_id=node.task_id, step=1)
            # 设置初始环节角色状态信息
            allocation = ProjectRoleAllocation.objects.filter(project_id=project.pk, node_id=node.pk)
            role_status_list = []
            for item in allocation:
                if item.can_brought:
                    come_status = 1
                else:
                    come_status = 9
                # 三期 - 不能直接创建， 在service中结束并走向下一环节的时候会创建角色状态，这里再创建一次就重复了
                ers = ExperimentRoleStatus.objects.filter(experiment_id=exp.id, node_id=item.node_id, path_id=path.pk,
                                                          role_id=item.role_id)
                if ers:  # 存在则更新
                    ers = ers.first()
                    ers.come_status = come_status
                    ers.save()
                else:  # 不存在则创建
                    ExperimentRoleStatus.objects.update_or_create(experiment_id=exp.id, node_id=item.node_id,
                                                                  path_id=path.pk, role_id=item.role_id,
                                                                  come_status=come_status)
                # role_status_list.append(ExperimentRoleStatus(experiment_id=exp.id, node_id=item.node_id,
                #                                              path_id=path.pk, role_id=item.role_id,
                #                                              come_status=come_status))

            # ExperimentRoleStatus.objects.bulk_create(role_status_list)
            # 设置环节中用户的角色状态
            member_roles = MemberRole.objects.filter(experiment_id=experiment_id, del_flag=0)
            for item in member_roles:
                ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                    role_id=item.role_id).update(user_id=item.user_id)

            # 环信id
            huanxin_id = easemob_result['data']['groupid']
            exp.huanxin_id = huanxin_id
            # 设置实验环节为开始环节,改变实验状态
            exp.node_id = first_node_id
            exp.path_id = path.pk
            exp.status = 2
            exp.save()

        # todo 优化
        user_roles = []
        role_ids = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, user_id=request.user.id,
                                                       path_id=path.pk,
                                                       node_id=exp.node_id).values_list('role_id', flat=True)
        roles = ProjectRole.objects.filter(id__in=role_ids)
        for role in roles:
            if ProjectRoleAllocation.objects.filter(project_id=exp.project_id, node_id=exp.node_id, role_id=role.id,
                                                    can_terminate=True).exists():
                can_terminate = True
            else:
                can_terminate = False
            user_roles.append({
                'id': role.id, 'name': role.name, 'can_terminate': can_terminate
            })

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'node': {
                'id': node.id, 'name': node.name, 'condition': node.condition, 'process_type': node.process.type},
            'huanxin_id': exp.huanxin_id, 'user_roles': user_roles, 'id': experiment_id, 'flow_id': project.flow_id
        }
        logger.info('api_experiment_start end:experiment_id=%s' % experiment_id)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_start Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除未开始实验
def api_experiment_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        data = request.POST.get("data")  # 实验id数组

        ids = json.loads(data)
        # 排除已经开始的实验
        Experiment.objects.exclude(status=2).filter(id__in=ids).update(del_flag=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 修改实验信息
def api_experiment_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id")  # 实验ID
        course_class_id = request.POST.get("course_class_id", None)  # 课程
        start_time = request.POST.get("start_time", None)  # 开始时间
        end_time = request.POST.get("end_time", None)  # 结束时间
        show_nickname = request.POST.get("show_nickname", None)  # 是否昵称显示组员
        data = request.POST.get("data", None)  # 角色分配数据
        logger.info('experiment_id:%s,course_class_id:%s,start_time:%s,end_time:%s,show_nickname:%s'
                    % (experiment_id, course_class_id, start_time, end_time, show_nickname))
        exp = Experiment.objects.filter(pk=experiment_id).first()

        # 将'true'或'false'转为1,0
        if show_nickname == 'true' or show_nickname == '1':
            show_nickname = 1
        else:
            show_nickname = 0

        data_list = json.loads(data)

        if exp:
            exp.course_class_id = course_class_id
            exp.start_time = start_time
            if end_time:
                exp.end_time = end_time
            exp.show_nickname = show_nickname
            exp.save()

            # 三期 - 进行中的实验也可以重新分配角色
            # if exp.status == 1:
            # 删除之前的角色分配信息
            MemberRole.objects.filter(experiment_id=experiment_id).update(del_flag=1)
            # (重新)设置小组成员角色分配信息
            for item in data_list:
                if item['user_id']:
                    MemberRole.objects.update_or_create(experiment_id=experiment_id, project_id=exp.project_id,
                                                        team_id=exp.team_id, role_id=item['id'],
                                                        user_id=item['user_id'], defaults={'del_flag': 0})

            # 三期， 实验进行中修改在当前环节生效

            # 环信创建群聊
            ids = list(
                TeamMember.objects.filter(team_id=exp.team_id,
                                          del_flag=const.DELETE_FLAG_NO).values_list('user_id', flat=True))
            if not ids:
                resp = code.get_msg(code.TEAM_MEMBER_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 注册所有的群组用户到环信群组
            easemob_success, easemob_result = easemob.add_groups_member(exp.huanxin_id, ids)
            logger.info(u'easemob create_groups:{}{}'.format(easemob_success, easemob_result))

            # 设置初始环节角色状态信息 按实验路径创建
            allocation = ProjectRoleAllocation.objects.filter(project_id=exp.project_id)

            for item in allocation:
                path = ExperimentTransPath.objects.filter(experiment_id=exp.id, node_id=item.node_id,
                                                          project_id=exp.project_id).first()
                if path:
                    if item.can_brought:
                        come_status = 1
                    else:
                        come_status = 9
                    # role_status_list.append(
                    #     ExperimentRoleStatus(experiment_id=exp.id, node_id=item.node_id, path_id=path.pk,
                    #                          role_id=item.role_id, come_status=come_status))
                    # 三期 - 不能直接创建， 在service中结束并走向下一环节的时候会创建角色状态，这里再创建一次就重复了
                    ers = ExperimentRoleStatus.objects.filter(experiment_id=exp.id, node_id=item.node_id,
                                                              path_id=path.id,
                                                              role_id=item.role_id)
                    if ers:  # 存在则更新
                        ers = ers.first()
                        ers.come_status = come_status
                        ers.save()
                    else:  # 不存在则创建
                        ExperimentRoleStatus.objects.update_or_create(experiment_id=exp.id, node_id=item.node_id,
                                                                      path_id=path.pk, role_id=item.role_id,
                                                                      come_status=come_status)
            # ExperimentRoleStatus.objects.bulk_create(role_status_list)

            # 设置环节中用户的角色状态
            member_roles = MemberRole.objects.filter(experiment_id=exp.id, project_id=exp.project_id, del_flag=0)
            for item in member_roles:
                ExperimentRoleStatus.objects.filter(experiment_id=exp.id,
                                                    role_id=item.role_id).update(user_id=item.user_id)
            clear_cache(exp.pk)
            resp = code.get_msg(code.SUCCESS)

        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)

        # 三期 - 到达指定环节还有角色没有设置提示设置角色
        node = FlowNode.objects.filter(pk=exp.node_id, del_flag=0).first()
        if node:
            # 已设置的角色
            role_list_has = MemberRole.objects.filter(experiment_id=experiment_id, project_id=exp.project_id,
                                                      del_flag=0)
            role_id_list_has = [item.role_id for item in role_list_has]  # 项目角色id
            # 环节需要的角色
            project_role_need = ProjectRoleAllocation.objects.filter(project_id=exp.project_id, node_id=node.pk, can_brought=False)
            role_id_list_need = [item.role_id for item in project_role_need]  # 流程角色id
            # 没有设置的角色名称
            role_name_not_set = []
            # 如果当前环节需要的角色还没有设置，则加入到role_name_not_set
            for role_id_need_temp in role_id_list_need:
                if role_id_need_temp not in role_id_list_has:
                    role_need_temp = ProjectRole.objects.filter(id=role_id_need_temp).first()
                    # 除掉老师观察者
                    if role_need_temp.name != const.ROLE_TYPE_OBSERVER:
                        role_name_not_set.append(role_need_temp.name)
            if len(role_name_not_set) > 0:
                logger.info('下一实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set))
                resp = code.get_msg(code.EXPERIMENT_ROLE_NOT_SET)
                resp['m'] = '下一实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 相关实验列表
def api_experiment_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数
        status = int(request.GET.get("status", 1))  # 实验状态

        # 获取当前用户所在的群组
        team_ids = TeamMember.objects.filter(user_id=request.user.id, del_flag=0).values_list('team_id', flat=True)
        # 过滤出与当前用户相关的实验(用户在实验小组内或用户为实验的创建者,实验为等待状态或进行中)
        if status == 1:
            qs = Experiment.objects.exclude(status=9).filter(
                Q(team_id__in=team_ids, del_flag=0) | Q(created_by=request.user.id))
            qs = qs.filter(del_flag=0)
        else:
            logger.info(status)
            qs = Experiment.objects.filter(
                Q(team_id__in=team_ids, del_flag=0) | Q(created_by=request.user.id))
            qs = qs.filter(status=9, del_flag=0)

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(pk__icontains=search))
            qs = qs.filter(del_flag=0)

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
                'id': item.id, 'name': u'{0} {1}'.format(item.id, item.name), 'show_nickname': item.show_nickname,
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


# 生成实验报告
def api_experiment_report_generate(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        user_id = request.GET.get("user_id", None)  # 用户
        user_id = user_id if user_id else request.user.id
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
            for item in paths:
                node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first()
                doc_list = []
                vote_status = []
                if node.process.type == 2:
                    # 如果是编辑
                    # 应用模板
                    contents = ExperimentDocContent.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                                   has_edited=True)
                    for d in contents:
                        doc_list.append({
                            'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                            'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                            'url': d.file.url if d.file else None
                        })
                    # 提交的文件
                    docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                        path_id=item.pk)
                    for d in docs:
                        sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
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
                    project_docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                                path_id=item.pk)
                    for d in project_docs:
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'signs': [],
                            'url':  d.file.url if d.file else None, 'content': d.content, 'file_type': d.file_type,
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
                elif node.process.type == 5:
                    # 如果是投票   三期 - 增加投票结果数量汇总
                    vote_status_0_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                        node_id=item.node_id,
                                                                        path_id=item.id, vote_status=0)
                    vote_status_0 = []
                    # 去掉老师观察者角色的数据
                    for item0 in vote_status_0_temp:
                        role_temp = ProjectRole.objects.filter(id=item0.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_0.append(item0)
                    vote_status_1_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                        node_id=item.node_id,
                                                                        path_id=item.id, vote_status=1)
                    vote_status_1 = []
                    # 去掉老师观察者角色的数据
                    for item1 in vote_status_1_temp:
                        role_temp = ProjectRole.objects.filter(id=item1.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_1.append(item1)
                    vote_status_2_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                        node_id=item.node_id,
                                                                        path_id=item.id, vote_status=2)
                    vote_status_2 = []
                    # 去掉老师观察者角色的数据
                    for item2 in vote_status_2_temp:
                        role_temp = ProjectRole.objects.filter(id=item2.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_2.append(item2)
                    vote_status_9_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                        node_id=item.node_id,
                                                                        path_id=item.id, vote_status=9)
                    vote_status_9 = []
                    # 去掉老师观察者角色的数据
                    for item9 in vote_status_9_temp:
                        role_temp = ProjectRole.objects.filter(id=item9.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_9.append(item9)
                    vote_status = [{'status': '同意', 'num': len(vote_status_1)},
                                   {'status': '不同意', 'num': len(vote_status_2)},
                                   {'status': '弃权', 'num': len(vote_status_9)},
                                   {'status': '未投票', 'num': len(vote_status_0)} ]
                    pass
                else:
                    # 提交的文件
                    docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                        path_id=item.id)
                    for d in docs:
                        sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'content': d.content,
                            'signs': list(sign_list), 'url': d.file.url if d.file else None, 'file_type': d.file_type
                        })
                # 消息
                messages = ExperimentMessage.objects.filter(experiment_id=experiment_id,
                                                            node_id=item.node_id, path_id=item.id).order_by('timestamp')
                message_list = []
                for m in messages:
                    audio = ExperimentMessageFile.objects.filter(pk=m.file_id).first()
                    message = {
                        'user_name': m.user_name, 'role_name': m.role_name,
                        'msg': m.msg, 'msg_type': m.msg_type, 'ext': json.loads(m.ext),
                        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if audio:
                        message['url'] = const.WEB_HOST + audio.file.url
                        message['filename'] = audio.file.name
                        message['secret'] = ''
                        message['length'] = audio.length
                    message_list.append(message)

                # 个人笔记
                note = ExperimentNotes.objects.filter(experiment_id=experiment_id,
                                                      node_id=item.node_id, created_by=user_id).first()
                node_list.append({
                    'docs': doc_list, 'messages': message_list, 'id': node.id, 'node_name': node.name,
                    'note': note.content if note else None, 'type': node.process.type if node.process else 0,
                    'vote_status': vote_status
                })
            experience = ExperimentExperience.objects.filter(experiment_id=exp.id, created_by=request.user.pk).first()
            experience_data = {'status': 1, 'content': ''}
            if experience:
                experience_data = {
                    'id': experience.id, 'content': experience.content, 'status': experience.status,
                    'created_by': user_simple_info(experience.created_by),
                    'create_time': experience.create_time.strftime('%Y-%m-%d')
                }
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'name': u'{0} {1}'.format(exp.id, exp.name), 'project_name': project.name,
                'team_name': team.name, 'members': member_list, 'flow_name': flow.name,
                'finish_time': exp.finish_time.strftime('%Y-%m-%d') if exp.finish_time else None,
                'start_time': exp.start_time.strftime('%Y-%m-%d') if exp.start_time else None,
                'end_time': exp.end_time.strftime('%Y-%m-%d') if exp.end_time else None,
                'create_time': exp.create_time.strftime('%Y-%m-%d'),
                'leader_name': leader.name if leader else None,
                'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
                                                      course_class.term) if course_class else None,
                'teacher': course_class.teacher1.name, 'nodes': node_list, 'experience': experience_data,
            }

        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_report_genetate Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验中上传文件
def api_experiment_docs_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        upload_file = request.FILES["file"]  # 文件
        experiment_id = request.POST.get("experiment_id")  # 实验
        node_id = request.POST.get("node_id")  # 环节
        role_id = request.POST.get("role_id", None)  # 角色id
        cmd = request.POST.get('cmd', None)
        logger.info('experiment_id:%s,node_id:%s,role_id:%s,cmd:%s' % (experiment_id, node_id, role_id, cmd))
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        if path is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if len(upload_file.name) > 60:
            resp = code.get_msg(code.UPLOAD_FILE_NAME_TOOLONG_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        file_type = tools.check_file_type(upload_file.name)
        doc = ExperimentDoc.objects.create(filename=upload_file.name, file=upload_file, experiment_id=experiment_id,
                                           node_id=node_id, role_id=role_id, path_id=path.id, file_type=file_type,
                                           created_by=request.user.id)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'id': doc.id, 'filename': doc.filename, 'file': doc.file.url if doc.file else None,
            'experiment_id': doc.experiment_id, 'node_id': doc.node_id, 'file_type': file_type,
            'created_by': user_simple_info(doc.created_by)
        }
        clear_cache(experiment_id)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_docs_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验中删除文件
def api_experiment_docs_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id")  # 实验
        node_id = request.POST.get("node_id")  # 环节
        doc_id = request.POST.get("doc_id")  # 文件
        logger.info('experiment_id:%s,node_id:%s' % (experiment_id, node_id))
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        if path is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        doc = ExperimentDoc.objects.filter(id=doc_id)
        if doc:
            doc.delete()

        resp = code.get_msg(code.SUCCESS)
        clear_cache(experiment_id)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_docs_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 创建实验
def api_experiment_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        team_id = request.POST.get("team_id")  # 小组

        project = Project.objects.filter(pk=project_id).first()
        team = Team.objects.filter(pk=team_id).first()

        # 判断项目是否存在
        if project:
            # 验证项目中是否有未配置的跳转项目
            if not check_jump_project(project):
                resp = code.get_msg(code.EXPERIMENT_JUMP_PROJECT_SETUP_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            name = team.name + ' ' + project.name
            with transaction.atomic():
                exp = Experiment.objects.create(project_id=project_id, team_id=team_id, name=name,
                                                cur_project_id=project_id, created_by=request.user.id)
                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {
                    'id': exp.id, 'name': u'{0} {1}'.format(exp.id, exp.name), 'project_id': exp.project_id,
                    'show_nickname': exp.show_nickname, 'start_time': exp.start_time, 'end_time': exp.end_time,
                    'team_id': exp.team_id, 'status': exp.status, 'created_by': user_simple_info(exp.created_by),
                    'course_class_id': exp.course_class_id, 'node_id': exp.node_id,
                    'create_time': exp.create_time.strftime('%Y-%m-%d')
                }
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_experiment_message_upload(request):
    """
        实验上传语音
    """
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.POST.get("experiment_id", None)
        node_id = request.POST.get("node_id", None)
        length = request.POST.get("length", None)
        file = request.FILES.get('file', None)

        if experiment_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if len(file.name) > 60:
            resp = code.get_msg(code.UPLOAD_FILE_NAME_TOOLONG_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        if node_id is None or exp.node_id != int(node_id):
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        if path is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        obj = ExperimentMessageFile.objects.create(experiment_id=experiment_id, user_id=request.user.pk,
                                                   node_id=node_id, file=file, length=length,
                                                   path_id=path.id, filename=file.name)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = obj.pk
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_message_upload Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_experiment_message_push(request):
    """
        实验发送消息
    """
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.POST.get("experiment_id", None)
        node_id = request.POST.get("node_id", None)
        role_id = request.POST.get("role_id", None)
        type = request.POST.get("type", None)
        msg = request.POST.get("msg", '')
        cmd = request.POST.get("cmd", None)
        param = request.POST.get("param", None)
        file_id = request.POST.get("file_id", None)
        data = request.POST.get('data', None)
        logger.info('experiment_id:%s,node_id:%s,role_id:%s,type:%s,cmd:%s,param:%s,file_id:%s,'
                    'data:%s' % (experiment_id, node_id, role_id, type, cmd, param, file_id, data))

        user = request.user

        if experiment_id is None or node_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        # todo 组长没有当前环节权限操作返回上一步提前结束等， 这里的判断是不是有问题
        # if exp.node_id != int(node_id):
        #     logger.info('=====================1869======================')
        #     resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        #     return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        if path is None:
            logger.info('=====================1875======================')
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 是否有结束环节的权限
        can_terminate = get_role_node_can_terminate(exp, exp.cur_project_id, node_id, role_id)

        # 如果启动了表达管理，验证当前角色发言次数，每申请一次最多发言三次，
        # 如果是结束权限者则可发言
        role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                          role_id=role_id, path_id=path.pk).first()
        logger.info('cmd:%s,control_status:%s,param:%s,type:%s' % (cmd, path.control_status, param, type))

        # if role_status is None:
        #     resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
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
        eps = ExperimentPositionStatus.objects.filter(experiment_id=exp.id, node_id=path.node_id, path_id=path.id,
                                                      role_id=role_id)
        if eps:
            experiment_position_status = eps.first()
            if experiment_position_status.sitting_status:  # 已入席
                role_status.sitting_status = const.SITTING_DOWN_STATUS

        target = [exp.huanxin_id, ]
        name = request.user.name
        from_obj = str(request.user.pk)
        role = ProjectRole.objects.filter(pk=role_id).first()
        # 三期 组长没有权限也可以执行一些操作
        # 当前环节不存在该角色 除了组长
        team = Team.objects.filter(id=exp.team_id).first()
        if role is None and user.id != team.leader:
            resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if role is None:
            role = ProjectRole()

        project = Project.objects.get(pk=exp.cur_project_id)
        node = FlowNode.objects.filter(pk=exp.node_id, del_flag=0).first()

        # 角色形象
        image = get_role_image(exp, role.image_id)
        if image is None and user.id != team.leader:
            resp = code.get_msg(code.EXPERIMENT_ROLE_IMAGE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 角色占位
        pos = get_role_position(exp, project, node, path, role)

        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        opt = None
        if type == const.MSG_TYPE_TXT:
            if node.process.type == 1:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
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
            ext = {'experiment_id': experiment_id, 'node_id': node_id, 'username': name,
                   'role_id': role_id, 'role_name': role.name, 'avatar': image['avatar'],
                   'cmd': const.ACTION_TXT_SPEAK, 'param': '', 'time': time, 'can_terminate': can_terminate,
                   'code_position': pos['code_position'] if pos else ''}

        elif type == const.MSG_TYPE_AUDIO:
            if pos is None:
                resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            # 音频
            if role_status.sitting_status == const.SITTING_UP_STATUS:
                resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if file_id is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            audio = ExperimentMessageFile.objects.filter(pk=file_id).first()
            if audio is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            msg_obj = {'type': const.MSG_TYPE_AUDIO, 'url': (const.WEB_HOST + audio.file.url) if audio.file else '',
                       'filename': audio.file.name, 'length': audio.length, 'secret': ''}

            ext = {'experiment_id': experiment_id, 'node_id': node_id, 'username': name,
                   'role_id': role_id, 'role_name': role.name, 'avatar': image['avatar'],
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
                result, opt = action_role_banned(exp, node_id, path.pk, data['control_status'])
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_MEET:
                # 约见
                result, opt = action_role_meet(exp, node_id, path.pk, role)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_APPLY_SPEAK:
                # 申请发言
                result, opt = True, {'role_id': role_id, 'role_name': role.name}
            elif cmd == const.ACTION_ROLE_APPLY_SPEAK_OPT:
                # 申请发言操作结果 data = {'msg_id':1,'role_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_role_speak_opt(exp, node_id, path.pk, data)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_DOC_APPLY_SHOW:
                # 申请展示
                result, opt = True, {'role_id': role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_REFRESH:
                # 刷新文件列表
                result, opt = True, {'role_id': role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_APPLY_SHOW_OPT:
                # 申请展示操作结果 data = {'msg_id':1,'doc_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_doc_apply_show_opt(exp, node_id, path.pk, data)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_DOC_SHOW:
                # 展示
                data = json.loads(data)
                result, opt = action_doc_show(data['doc_id'])
            elif cmd == const.ACTION_ROLE_LETOUT:
                # 送出 data [1, 2, 3, ...]
                role_ids = json.loads(data)
                result, lst = action_role_letout(exp, node, path.pk, role_ids)
                opt = {'data': lst}
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_LETIN:
                # 请入 data [1, 2, 3, ...]
                role_ids = json.loads(data)
                result, lst = action_role_letin(exp, node_id, path.pk, role_ids)
                opt = {'data': lst}
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_SITDOWN:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 坐下
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_sitdown(exp, node_id, path.pk, role, pos)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_STAND:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 起立
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_stand(exp, node_id, path.pk, role, pos)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_HIDE:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                # 退席
                if role_status.sitting_status == const.SITTING_UP_STATUS:
                    resp = code.get_msg(code.MESSAGE_SITTING_UP_CANNOT_SPEAKER)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_hide(exp, node_id, path.pk, role, pos)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_SHOW:
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 入席
                if role_status.sitting_status == const.SITTING_DOWN_STATUS:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_HAS_IN_POSITION)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                # 占位状态
                position_status = ExperimentPositionStatus.objects.filter(experiment_id=exp.id, node_id=node_id,
                                                                          path_id=path.pk,
                                                                          position_id=pos['position_id'],
                                                                          sitting_status=const.SITTING_DOWN_STATUS).exists()
                if position_status:
                    resp = code.get_msg(code.EXPERIMENT_POSITION_HAS_USE)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_show(exp, node_id, path.pk, role, pos)
                clear_cache(exp.pk)
            elif cmd == const.ACTION_DOC_APPLY_SUBMIT:
                # 申请提交
                result, opt = True, {'role_id': role_id, 'role_name': role.name}
            elif cmd == const.ACTION_DOC_APPLY_SUBMIT_OPT:
                # 申请提交操作结果 data = {'msg_id':1,'role_id': 1, 'result': 1}
                data = json.loads(data)
                result, opt = action_doc_apply_submit_opt(exp, node_id, path.pk, data)
                clear_cache(exp.pk)
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
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                result, opt = action_role_toward_report(exp, node_id, path.pk, role, pos)
                if not result:
                    return HttpResponse(json.dumps(opt, ensure_ascii=False), content_type="application/json")
                clear_cache(exp.pk)
            elif cmd == const.ACTION_ROLE_EDN_REPORT:
                # 走下发言席 data = {}
                if pos is None:
                    resp = code.get_msg(code.EXPERIMENT_ROLE_POSITION_NOT_EXIST)
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
            ext = {'experiment_id': experiment_id, 'node_id': node_id, 'username': name,
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
            message = ExperimentMessage.objects.create(experiment_id=exp.pk, user_id=user.pk, role_id=role_id,
                                                       node_id=node_id, file_id=file_id, msg=msg, msg_type=type,
                                                       path_id=path.id, user_name=name, role_name=role.name,
                                                       ext=json.dumps(ext))
        ext['id'] = message.pk
        ext['opt_status'] = False

        flag, result = easemob.send_message(easemob.TARGET_TYPE_GROUP, target, msg_obj, from_obj, ext)
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


# 实验环节聊天消息列表
def api_experiment_node_messages(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        node_id = request.GET.get("node_id", None)  # 环节id
        is_paging = int(request.GET.get('is_paging', 1))  # 是否进行分页（1，分页；0，不分页）
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
            data = get_node_path_messages(exp, node_id, path.pk, is_paging, page, size)

            for i in range(len(data['results'])):
                file_id = data['results'][i]['file_id']
                mid = data['results'][i]['id']
                m_ext = data['results'][i]['ext']
                opt_status = data['results'][i]['opt_status']

                # 更新扩展
                ext = json.loads(m_ext)
                ext['id'] = mid
                if opt_status == 1:
                    ext['opt_status'] = True
                else:
                    ext['opt_status'] = False

                data['results'][i]['type'] = 'groupchat'
                data['results'][i]['ext'] = ext
                data['results'][i]['to'] = exp.huanxin_id

                # 音频文件
                if file_id:
                    audio = ExperimentMessageFile.objects.filter(pk=file_id).first()
                    if audio:
                        data['results'][i]['url'] = const.WEB_HOST + audio.file.url
                        data['results'][i]['filename'] = audio.file.name
                        data['results'][i]['secret'] = ''
                        data['results'][i]['length'] = audio.length

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_messages Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_experiment_messages(request):
    """
    实验所有消息，按环节分组
    :param request:
    :return:
    """
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            paths = ExperimentTransPath.objects.filter(experiment_id=exp.id)
            node_list = []
            for item in paths:
                messages = ExperimentMessage.objects.filter(experiment_id=experiment_id,
                                                            node_id=item.node_id, path_id=item.id).order_by('timestamp')
                message_list = []
                for m in messages:
                    ext = json.loads(m.ext)
                    ext['id'] = m.id
                    ext['opt_status'] = m.opt_status
                    message = {
                        'id': m.id, 'from': m.user_id, 'to': exp.huanxin_id, 'msg_type': m.msg_type,
                        'data': m.msg, 'type': 'groupchat', 'ext': ext
                    }
                    if m.file_id:
                        audio = ExperimentMessageFile.objects.filter(pk=m.file_id).first()
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
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_messages Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节用户角色状态查询
def api_experiment_role_status(request):
    resp = auth_check(request, 'GET')
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.GET.get("experiment_id")  # 实验任务id
        node_id = request.GET.get("node_id")  # 环节id

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.get(pk=exp.cur_project_id)
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()
        node = FlowNode.objects.filter(pk=node_id, del_flag=0).first()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = get_all_roles_status(exp, project, node, path)
    except Exception as e:
        logger.exception('experiment_role_status Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节用户可签字角色查询
def api_experiment_request_sign_roles(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id
        role_id = request.GET.get("role_id", 0)  # 角色id
        exp = Experiment.objects.filter(pk=experiment_id).first()

        # 判断实验是否存在以及实验当前环节是否是node_id
        if exp and exp.node_id == int(node_id):
            path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

            role_status_list = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=exp.node_id,
                                                                   path_id=path.pk, sitting_status=2)
            role_list = []
            for item in role_status_list:
                if item.role_id == int(role_id):
                    continue

                role = ProjectRole.objects.get(pk=item.role_id)
                # 三期 老师以实验指导登录进来，老师只观察只给一个观察者的角色;
                # 老师以实验者登录进来，要去掉老师的观察者角色
                if role.name != const.ROLE_TYPE_OBSERVER:
                    role_list.append({'id': role.id, 'name': role.name})
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = role_list
        elif exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            logger.info('=====================2422======================')
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_request_sign_roles Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询实验心得list
def api_experiment_experience_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        # 判断实验是否存在
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0)
        if exp:
            lst = ExperimentExperience.objects.filter(experiment_id=experiment_id)
            data = []
            for item in lst:
                data.append({
                    'id': item.id, 'content': item.content, 'created_by': user_simple_info(item.created_by),
                    'create_time': item.create_time.strftime('%Y-%m-%d'), 'status': item.status
                })
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_experience_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询实验心得
def api_experiment_experience_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        # 判断实验是否存在
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            instance = ExperimentExperience.objects.filter(experiment_id=experiment_id,
                                                           created_by=request.user.id).first()
            resp = code.get_msg(code.SUCCESS)
            if instance:
                resp['d'] = {
                    'id': instance.id, 'content': instance.content, 'created_by': user_simple_info(instance.created_by),
                    'create_time': instance.create_time.strftime('%Y-%m-%d'), 'status': instance.status
                }
            else:
                resp['d'] = {'status': 1, 'content': ''}
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_experiment_experience_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验流程图路径
def api_experiment_trans_path(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        # 判断实验是否存在
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            if exp.status == const.EXPERIMENT_FINISHED:
                node = {'is_finished': True}
            else:
                next_node = FlowNode.objects.filter(pk=exp.node_id).first()
                node = {'node_id': next_node.pk, 'task_id': next_node.task_id,
                        'name': next_node.name, 'is_finished': False}

            project = Project.objects.get(pk=exp.cur_project_id)
            paths = ExperimentTransPath.objects.filter(experiment_id=exp.id,
                                                       project_id=exp.cur_project_id).values_list('task_id', flat=True)
            flow = Flow.objects.get(pk=project.flow_id)
            xml = bpmn_color(flow.xml, list(paths))

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'exp_id': exp.pk, 'exp_name': exp.name, 'flow_id': flow.pk, 'flow_name': flow.name,
                         'xml': xml, 'node': node}
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_experiment_trans_path Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验流程路径
def api_experiment_node_path(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        # 判断实验是否存在
        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = get_experiment_path(exp)
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_experiment_node_path Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_experiment_path_messages(request):
    """
    实验环节路径消息
    :param request:
    :return:
    """
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验ID
        node_id = request.GET.get("node_id", None)  # 环节id
        path_id = request.GET.get("path_id", None)  # 环节id
        is_paging = int(request.GET.get('is_paging', 1))  # 是否进行分页（1，分页；0，不分页）
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp:
            data = get_node_path_messages(exp, node_id, path_id, is_paging, page, size)
            for i in range(len(data['results'])):
                file_id = data['results'][i]['file_id']
                mid = data['results'][i]['id']
                m_ext = data['results'][i]['ext']
                opt_status = data['results'][i]['opt_status']

                # 更新扩展
                ext = json.loads(m_ext)
                ext['id'] = mid
                if opt_status == 1:
                    ext['opt_status'] = True
                else:
                    ext['opt_status'] = False

                data['results'][i]['type'] = 'groupchat'
                data['results'][i]['ext'] = ext
                data['results'][i]['to'] = exp.huanxin_id

                # 音频文件
                if file_id:
                    audio = ExperimentMessageFile.objects.filter(pk=file_id).first()
                    if audio:
                        data['results'][i]['url'] = const.WEB_HOST + audio.file.url
                        data['results'][i]['filename'] = audio.file.name
                        data['results'][i]['secret'] = ''
                        data['results'][i]['length'] = audio.length

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = data
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_path_messages Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验结果
def api_experiment_result(request):
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
            for item in paths:
                # 个人笔记
                note = ExperimentNotes.objects.filter(experiment_id=experiment_id,
                                                      node_id=item.node_id, created_by=user_id).first()

                # 角色项目素材
                project_doc_list = []
                operation_guide_list = []
                project_tips_list = []

                doc_ids = FlowNodeDocs.objects.filter(flow_id=flow.pk,
                                                      node_id=item.node_id).values_list('doc_id', flat=True)
                if doc_ids:
                    operation_docs = FlowDocs.objects.filter(id__in=doc_ids, usage__in=(1, 2, 3))
                    for d in operation_docs:
                        url = ''
                        if d.file:
                            url = d.file.url
                        if d.usage == 1:
                            operation_guide_list.append({
                                'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                                'content': d.content, 'url': url, 'file_type': d.file_type
                            })
                        else:
                            project_doc_list.append({
                                'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                                'content': d.content, 'url': url, 'file_type': d.file_type
                            })
                            
                # 获取该环节角色分配项目素材id
                doc_ids = ProjectDocRole.objects.filter(project_id=item.project_id,
                                                        node_id=item.node_id).values_list('doc_id', flat=True)

                if doc_ids:
                    # logger.info(doc_ids)
                    project_docs = ProjectDoc.objects.filter(id__in=doc_ids)
                    for d in project_docs:
                        if d.usage in [3, 4, 5, 7]:
                            is_exist = False
                            if d.usage == 3:
                                for t in project_doc_list:
                                    if d.name == t['name']:
                                        is_exist = True
                                        break
                            if not is_exist:
                                project_doc_list.append({
                                    'id': d.id, 'name': d.name, 'type': d.type, 'usage': d.usage,
                                    'content': d.content, 'url': d.file.url, 'file_type': d.file_type
                                })

                node = FlowNode.objects.filter(pk=item.node_id, del_flag=0).first()
                doc_list = []
                vote_status = []
                if node.process.type == 2:
                    # 如果是编辑
                    # 应用模板
                    contents = ExperimentDocContent.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                                   has_edited=True)
                    for d in contents:
                        doc_list.append({
                            'id': d.doc_id, 'filename': d.name, 'content': d.content, 'file_type': d.file_type,
                            'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                            'url': d.file.url if d.file else None
                        })
                    # 提交的文件
                    docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                        path_id=item.pk)
                    for d in docs:
                        sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                            'signs': list(sign_list), 'url': d.file.url if d.file else None
                        })
                elif node.process.type == 3:
                    # 如果是展示
                    # project_docs = ProjectDoc.objects.filter(project_id=exp.project_id, usage=4)
                    # for d in project_docs:
                    #     doc_list.append({
                    #         'id': d.id, 'filename': d.name, 'signs': [],
                    #         'url': d.file.url, 'content': d.content, 'file_type': d.file_type,
                    #     })
                    project_docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
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
                    #         'role_name': '', 'node_name': node.name if node else None,'created_by': None,
                    #         'signs': [{'sign_status': d.sign_status, 'sign': d.sign}],
                    #     })
                # elif node.process.type == 4:
                #     experience = ExperimentExperience.objects.filter(experiment_id=exp.id,
                #                                                      created_by=request.user.pk).first()
                #     experience_data = {'status': 1, 'content': ''}
                #     if experience:
                #         experience_data = {
                #             'id': experience.id, 'content': experience.content, 'status': experience.status,
                #             'created_by': user_simple_info(experience.created_by),
                #             'create_time': experience.create_time.strftime('%Y-%m-%d')
                #         }
                elif node.process.type == 5:
                    # 如果是投票   三期 - 增加投票结果数量汇总  todo 去掉老师观察者的数量 WTF
                    vote_status_0_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                        node_id=item.node_id,
                                                                        path_id=item.id, vote_status=0)
                    vote_status_0 = []
                    # 去掉老师观察者角色的数据
                    for item0 in vote_status_0_temp:
                        role_temp = ProjectRole.objects.filter(id=item0.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_0.append(item0)
                    vote_status_1_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                             node_id=item.node_id,
                                                                             path_id=item.id, vote_status=1)
                    vote_status_1 = []
                    # 去掉老师观察者角色的数据
                    for item1 in vote_status_1_temp:
                        role_temp = ProjectRole.objects.filter(id=item1.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_1.append(item1)
                    vote_status_2_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                             node_id=item.node_id,
                                                                             path_id=item.id, vote_status=2)
                    vote_status_2 = []
                    # 去掉老师观察者角色的数据
                    for item2 in vote_status_2_temp:
                        role_temp = ProjectRole.objects.filter(id=item2.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_2.append(item2)
                    vote_status_9_temp = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id,
                                                                             node_id=item.node_id,
                                                                             path_id=item.id, vote_status=9)
                    vote_status_9 = []
                    # 去掉老师观察者角色的数据
                    for item9 in vote_status_9_temp:
                        role_temp = ProjectRole.objects.filter(id=item9.role_id).first()
                        if role_temp.name != const.ROLE_TYPE_OBSERVER:
                            vote_status_9.append(item9)
                    vote_status = [{'status': '未投票', 'num': len(vote_status_0)},
                                   {'status': '同意', 'num': len(vote_status_1)},
                                   {'status': '不同意', 'num': len(vote_status_2)},
                                   {'status': '弃权', 'num': len(vote_status_9)}]
                    pass
                else:
                    # 提交的文件
                    docs = ExperimentDoc.objects.filter(experiment_id=experiment_id, node_id=item.node_id,
                                                        path_id=item.id)
                    for d in docs:
                        sign_list = ExperimentDocSign.objects.filter(doc_id=d.pk).values('sign', 'sign_status')
                        doc_list.append({
                            'id': d.id, 'filename': d.filename, 'content': d.content, 'file_type': d.file_type,
                            'signs': list(sign_list), 'url': d.file.url if d.file else None
                        })
                # 消息
                messages = ExperimentMessage.objects.filter(experiment_id=experiment_id,
                                                            node_id=item.node_id, path_id=item.id).order_by('timestamp')
                message_list = []
                for m in messages:
                    audio = ExperimentMessageFile.objects.filter(pk=m.file_id).first()
                    message = {
                        'user_name': m.user_name, 'role_name': m.role_name,
                        'msg': m.msg, 'msg_type': m.msg_type, 'ext': json.loads(m.ext),
                        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if audio:
                        message['url'] = const.WEB_HOST + audio.file.url
                        message['filename'] = audio.file.name
                        message['secret'] = ''
                        message['length'] = audio.length
                    message_list.append(message)

                node_list.append({
                    'docs': doc_list, 'messages': message_list, 'id': node.id, 'node_name': node.name,
                    'project_docs': project_doc_list,
                    'operation_guides': operation_guide_list,
                    'project_tips_list': project_tips_list,
                    'note': note.content if note else None, 'type': node.process.type if node.process else 0,
                    'vote_status': vote_status
                })

            detail = {'name': u'{0} {1}'.format(exp.id, exp.name), 'project_name': project.name,
                      'team_name': team.name, 'members': member_list, 'teacher': course_class.teacher1.name,
                      'finish_time': exp.finish_time.strftime('%Y-%m-%d') if exp.finish_time else None,
                      'start_time': exp.start_time.strftime('%Y-%m-%d') if exp.start_time else None,
                      'end_time': exp.end_time.strftime('%Y-%m-%d') if exp.end_time else None,
                      'create_time': exp.create_time.strftime('%Y-%m-%d'),
                      'leader_name': leader.name if leader else None, 'flow_name': flow.name, 'flow_xml': flow.xml,
                      'course_class': u'{0} {1} {2}'.format(course_class.name, course_class.no,
                                                            course_class.term) if course_class else None}
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'detail': detail, 'nodes': node_list}
        else:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_result Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验环节素材
def api_experiment_node_docs(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id")  # 实验任务id
        path_id = request.GET.get("path_id")  # 环节id

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        path = ExperimentTransPath.objects.filter(pk=path_id).first()
        if path is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=path.node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 获取该环节所有素材
        data = get_node_docs(exp, path.project_id, path.node_id)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_docs Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 开始实验跳转任务
def api_experiment_jump_start(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id")  # 实验ID
        project_id = request.POST.get("project_id")
        data = request.POST.get("data", None)  # 角色分配数据
        logger.info('api_experiment_jump_start:experiment_id=%s,project_id=%s' % (experiment_id, project_id))
        exp = Experiment.objects.filter(pk=experiment_id).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        data_list = json.loads(data)
        project = Project.objects.get(pk=project_id)
        team = Team.objects.filter(pk=exp.team_id).first()
        if not team:
            resp = code.get_msg(code.TEAM_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        transition = FlowTrans.objects.filter(flow_id=project.flow_id,
                                              incoming__startswith='StartEvent').first()
        if transition is None:
            resp = code.get_msg(code.FLOW_DIRECTION_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        tran_id = transition.pk
        with transaction.atomic():
            # 设置小组成员角色分配信息
            for item in data_list:
                if item['user_id']:
                    # 设置新的实验的小组成员角色分配
                    MemberRole.objects.update_or_create(experiment_id=experiment_id, project_id=project_id,
                                                        team_id=exp.team_id, role_id=item['id'],
                                                        user_id=item['user_id'], defaults={'del_flag': 0})

        clear_cache(exp.pk)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'tran_id': tran_id, 'project_id': project_id
        }
        clear_cache(experiment_id)

        # 三期 - 到达指定环节还有角色没有设置提示设置角色
        next_node = FlowNode.objects.filter(flow_id=transition.flow_id, task_id=transition.outgoing).first()
        node = FlowNode.objects.filter(pk=exp.node_id, del_flag=0).first()
        if node:
            # 已设置的角色
            role_list_has = MemberRole.objects.filter(experiment_id=experiment_id, project_id=project_id,
                                                      del_flag=0)
            role_id_list_has = [item.role_id for item in role_list_has]  # 项目角色id
            # 环节需要的角色
            project_role_need = ProjectRoleAllocation.objects.filter(project_id=project_id, node_id=next_node.pk)
            role_id_list_need = [item.role_id for item in project_role_need]  # 流程角色id
            # 没有设置的角色名称
            role_name_not_set = []
            # 如果当前环节需要的角色还没有设置，则加入到role_name_not_set
            for role_id_need_temp in role_id_list_need:
                if role_id_need_temp not in role_id_list_has:
                    role_need_temp = ProjectRole.objects.filter(id=role_id_need_temp).first()
                    # 除掉老师观察者
                    if role_need_temp.name != const.ROLE_TYPE_OBSERVER:
                        role_name_not_set.append(role_need_temp.name)
            if len(role_name_not_set) > 0:
                logger.info('当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set))
                resp['c'] = code.get_msg(code.EXPERIMENT_ROLE_NOT_SET)
                resp['m'] = '当前实验环节，以下角色还没有设置: ' + ','.join(role_name_not_set)
                # data['role_not_set'] = resp['m']
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        logger.info('api_experiment_jump_start end:experiment_id=%s,project_id=%s' % (experiment_id, project_id))
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_experiment_jump_start Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 待安排报告角色列表
def api_experiment_role_schedule_report_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id")  # 环节id
        exp = Experiment.objects.filter(pk=experiment_id).first()

        # 判断实验是否存在以及实验当前环节是否是node_id
        if exp and exp.node_id == int(node_id):
            path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

            role_ids = ExperimentReportStatus.objects.filter(experiment_id=experiment_id, node_id=exp.node_id,
                                                             path_id=path.pk).exclude(schedule_status=0
                                                                                      ).values_list('role_id', flat=True)

            role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                              path_id=path.pk)
            role_list = []
            for item in role_status:
                if item.role_id not in role_ids:
                    role = ProjectRole.objects.filter(pk=item.role_id).first()
                    if role.name != const.ROLE_TYPE_OBSERVER:
                        role_list.append({'id': role.id, 'name': role.name})

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = role_list

        elif exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
        else:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_wait_report_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验投票环节状态
def api_experiment_vote_status(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id")  # 环节id
        role_id = request.GET.get("role_id", None)  # 角色id

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

        has_vote = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                       path_id=path.pk, role_id=role_id, vote_status=0).exists()
        if path.vote_status == 1:
            end_vote = False
        else:
            end_vote = True

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'id': exp.id, 'has_vote': False if has_vote else True, 'end_vote': end_vote}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_vote_status Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 实验下一个环节详情
def api_experiment_node_next_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get('experiment_id', None)  # 实验id
        node_id = request.GET.get("node_id", None)  # 环节id

        exp = Experiment.objects.filter(pk=experiment_id, del_flag=0).first()
        if exp is None:
            resp = code.get_msg(code.EXPERIMENT_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 验证环节是否存在
        node = FlowNode.objects.filter(pk=node_id).first()
        if node is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 路径
        path = ExperimentTransPath.objects.filter(experiment_id=experiment_id).last()

        user_id = request.user.id
        # 判断该实验环节是否存在该角色
        role_status = ExperimentRoleStatus.objects.filter(experiment_id=experiment_id, node_id=node_id,
                                                          path_id=path.pk, user_id=user_id).first()
        if role_status is None:
            resp = code.get_msg(code.EXPERIMENT_NODE_ROLE_NOT_EXIST)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        # 当前用户可选角色
        role_list = get_roles_status_by_user(exp, path, user_id)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'roles': role_list, 'id': exp.id, 'name': exp.name,
            'node': {'id': node.id, 'name': node.name, 'condition': node.condition}
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 老师任务列表
def api_experiment_teacher_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        course_class_id = request.GET.get("course_class_id", None)  # 课程ID
        course_class = CourseClass.objects.get(pk=course_class_id)
        exps = Experiment.objects.filter(course_class_id=course_class_id, del_flag=0)  # 根据课堂查询实验任务集合
        data = []
        for exp in exps:
            project = Project.objects.filter(pk=exp.project_id).first()
            created_by = Tuser.objects.filter(pk=exp.created_by).first()
            # 是否评价:所有角色都评价则已评价
            # 查询所有角色
            sql = '''select a.user_id,c.name role_name,d.name user_name 
                        from t_member_role  a 
                        LEFT JOIN t_experiment b on a.experiment_id = b.id 
                        LEFT JOIN t_project_role c on a.role_id = c.id
                        LEFT JOIN t_user d on a.user_id = d.id'''
            count_sql = '''SELECT count(1) from t_member_role  a 
                        LEFT JOIN t_experiment b on a.experiment_id = b.id 
                        LEFT JOIN t_project_role c on a.role_id = c.id
                        LEFT JOIN t_user d on a.user_id = d.id'''
            where_sql = ' WHERE b.del_flag = 0 and a.experiment_id = %s' % exp.id

            sql += where_sql
            count_sql += where_sql
            logger.info(sql)
            user_role_list = query.pagination_page(sql, ['user_id', 'role_name', 'user_name'],
                                         count_sql, 1, 1000)

            evaluate = True
            for user_role in user_role_list['results']:
                # 判断角色是否评价
                evaluate_exp = EvaluateExperiment.objects.filter(experiment_id=exp.id, user_id=user_role['user_id'])
                if not evaluate_exp:
                    evaluate = False
                    break
                # evaluate_node = EvaluateNode.objects.filter(experiment_id=exp.id, user_id=user_role['user_id'])
                # if not evaluate_node:
                #     evaluate = False
                #     break

            data.append({'id': exp.id, 'name': exp.name, 'project_name': project.name, 'course_class_name': course_class.name,
                         'create_time': exp.create_time.strftime('%Y-%m-%d'), 'created_by_name': created_by.name,
                         'created_by_type': created_by.type, 'status': exp.status, 'evaluate': evaluate})

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询点评信息列表
def api_experiment_evaluate_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        evaluate_type = EvaluateType.objects.all()  # 查询所有的评价分类
        data = []
        for i in evaluate_type:
            evaluate = EvaluatePool.objects.filter(evaluate_type=i)  # 根据分类查询分类下的评语
            if not evaluate:
                continue
            evaluate_data = []
            for j in evaluate:
                evaluate_data.append({'id': j.id, 'evaluate_level': j.evaluate_level,
                                      'evaluate_content': j.evaluate_content})
            data.append({'evaluate_type': i.label, 'evaluate': evaluate_data})

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 总体评价
def api_experiment_evaluate(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id", None)  # 实验id
        user_ids = request.POST.get("user_id", None)  # 用户id, 多个用英文逗号连接
        content = request.POST.get("content", None)  # 内容
        sys_score = request.POST.get("sys_score", None)  # 系统评分
        teacher_score = request.POST.get("teacher_score", None)  # 教师评分
        create_by_id = request.POST.get("create_by_id", None)  # 提交人
        # 环节评价json字符串，如[{"node_id":2477,"content":"good"},{"node_id":2487,"content":"good"}]
        evaluate_node = request.POST.get("evaluate_node", None)

        # 参数check
        if None in (experiment_id, user_ids, content, create_by_id):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        user_id_arr = user_ids.split(',')
        for user_id in user_id_arr:
            ee = EvaluateExperiment.objects.filter(experiment_id=experiment_id, user_id=user_id)
            if ee:  # 存在则更新
                ee = ee.first()
                if content:
                    ee.content = content
                ee.sys_score = sys_score
                ee.teacher_score = teacher_score
                ee.create_by_id = create_by_id
                ee.save()
            else:  # 不存在则创建
                EvaluateExperiment.objects.update_or_create(experiment_id=experiment_id, user_id=user_id,
                                                            content=content, sys_score=sys_score,
                                                            teacher_score=teacher_score, create_by_id=create_by_id)
            evaluate_node_list = json.loads(evaluate_node)
            for en in evaluate_node_list:
                en_vo = EvaluateNode.objects.filter(experiment_id=experiment_id, node_id=en['node_id'], user_id=user_id)
                if en_vo:  # 存在则更新
                    en_vo = en_vo.first()
                    en_vo.content = en['content']
                    en_vo.create_by_id = create_by_id
                    en_vo.save()
                else:  # 不存在则创建
                    EvaluateNode.objects.update_or_create(experiment_id=experiment_id, node_id=en['node_id'],
                                                          user_id=user_id, content=en['content'],
                                                          create_by_id=create_by_id)

        data = {}
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 环节评价, 不用这个接口了，统一api_experiment_evaluate一个接口评价
def api_experiment_node_evaluate(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.POST.get("experiment_id", None)  # 实验id
        node_id = request.POST.get("node_id", None)  # 环节id
        user_id = request.POST.get("user_id", None)  # 用户id
        content = request.POST.get("content", None)  # 内容
        sys_score = request.POST.get("sys_score", None)  # 系统评分
        teacher_score = request.POST.get("teacher_score", None)  # 教师评分
        create_by_id = request.POST.get("create_by_id", None)  # 提交人

        # 参数check
        if None in (experiment_id, user_id, content, create_by_id):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        EvaluateExperiment.objects.update_or_create(experiment_id=experiment_id, user_id=user_id,
                                                    sys_score=sys_score, teacher_score=teacher_score,
                                                    create_by_id=create_by_id)

        e, flag = EvaluateNode.objects.update_or_create(experiment_id=experiment_id, node_id=node_id, user_id=user_id,
                                                        content=content, sys_score=sys_score,
                                                        teacher_score=teacher_score, create_by_id=create_by_id)
        data = {}
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期教师评价根据实验任务查询所有人员评价得分列表
def api_experiment_evaluate_user_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id", None)  # 实验任务id

        sql = '''select a.experiment_id, d.id user_id, d.username, d.name user_name, e.name class_name, 
                  d.nickname, c.name role_name, f.teacher_score, f.sys_score
                from t_member_role  a 
                LEFT JOIN t_experiment b on a.experiment_id = b.id 
                LEFT JOIN t_project_role c on a.role_id = c.id
                LEFT JOIN t_user d on a.user_id = d.id
                LEFT JOIN t_class e on d.tclass_id = e.id
                LEFT JOIN t_evaluate_experiment f on a.experiment_id = f.experiment_id and d.id = f.user_id'''
        count_sql = '''SELECT count(1) from t_member_role  a 
                LEFT JOIN t_experiment b on a.experiment_id = b.id 
                LEFT JOIN t_project_role c on a.role_id = c.id
                LEFT JOIN t_user d on a.user_id = d.id
                LEFT JOIN t_class e on d.tclass_id = e.id
                LEFT JOIN t_evaluate_experiment f on a.experiment_id = f.experiment_id and d.id = f.user_id'''
        where_sql = ' WHERE a.experiment_id = %s' % experiment_id

        sql += where_sql
        count_sql += where_sql
        logger.info(sql)
        data = query.pagination_page(sql, ['experiment_id', 'user_id', 'username', 'user_name', 'class_name',
                                           'nickname', 'role_name', 'teacher_score', 'sys_score'],
                                     count_sql, 1, 1000)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = data['results']
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期教师评价根据实验任务查询所有环节列表
def api_experiment_node_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id", None)  # 实验任务id

        experiment = Experiment.objects.get(pk=experiment_id)  # 实验

        project = Project.objects.get(pk=experiment.project_id)  # 实验项目

        # flow = Flow.objects.get(pk=project.flow_id)  # 流程

        node_list = FlowNode.objects.filter(flow_id=project.flow_id, del_flag=0)  # 根据流程id查询环节

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = [{'node_id': node.id, 'node_name': node.name} for node in node_list]
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查看点评详情
def api_experiment_evaluate_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        experiment_id = request.GET.get("experiment_id", None)  # 实验任务id
        user_id = request.GET.get("user_id", None)  # user_id

        # 总体评价
        evaluate_exp = EvaluateExperiment.objects.filter(experiment_id=experiment_id, user_id=user_id)
        if evaluate_exp:
            evaluate_exp = evaluate_exp.first()
        else:
            evaluate_exp = EvaluateExperiment()
        # 环节评价
        sql = '''SELECT a.node_id node_id, b.`name` node_name, a.content content 
                from t_evaluate_node a LEFT JOIN t_flow_node b on a.node_id = b.id
                where a.experiment_id = %s and a.user_id = %s
                ORDER BY b.`name`''' % (experiment_id, user_id)

        count_sql = '''SELECT count(1)
                from t_evaluate_node a LEFT JOIN t_flow_node b on a.node_id = b.id
                where a.experiment_id = %s and a.user_id = %s
                ORDER BY b.`name`''' % (experiment_id, user_id)

        logger.info(sql)

        evaluate_node = query.pagination_page(sql, ['node_id', 'node_name', 'content'], count_sql, 1, 1000)

        # evaluate_node = EvaluateNode.objects.filter(experiment_id=experiment_id, user_id=user_id).order_by('node_id')

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'evaluate_experiment': {'content': evaluate_exp.content, 'sys_score': evaluate_exp.sys_score,
                                    'teacher_score': evaluate_exp.teacher_score},
            'evaluate_node': evaluate_node['results']
        }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_experiment_node_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

