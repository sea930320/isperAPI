#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging
from docx import Document
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponse
from django.db import transaction
from account.service import user_simple_info
from project.models import *
from datetime import datetime
from team.models import Team
from group.models import AllGroups
from account.models import TCompany
from workflow.models import *
from experiment.models import Experiment
from course.models import Course, CourseClass
from utils.request_auth import auth_check
from utils import query, code, public_fun, tools
from django.core.cache import cache
from utils.permission import permission_check
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


# 项目上传素材
def api_project_docs_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id", None)  # 环节ID
        upload_file = request.FILES.get("file", None)  # 文件

        project = Project.objects.filter(pk=project_id).first()
        if project_id is None or upload_file is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
        elif project is None:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        else:
            if len(upload_file.name) > 60:
                resp = code.get_msg(code.UPLOAD_FILE_NAME_TOOLONG_ERROR)
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

            doc = ProjectDoc.objects.create(project_id=project_id, file=upload_file, name=upload_file.name,
                                            content=content, file_type=file_type)
            if project.step < const.PRO_STEP_3:
                project.step = const.PRO_STEP_3
                project.save()
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': doc.id, 'name': doc.name, 'file': doc.file.url
            }
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_project_docs_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 流程删除素材
def api_project_docs_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        doc_id = request.POST.get("doc_id", None)  # 素材ID
        if doc_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        with transaction.atomic():
            doc = ProjectDoc.objects.filter(id=doc_id).first()
            if doc:
                # 删除项目环节素材角色分配,不用处理 todo update is done
                ProjectDocRole.objects.filter(project_id=doc.project_id, doc_id=doc.pk).delete()
                # 删除素材
                ProjectDoc.objects.filter(id=doc_id).delete()
                project = Project.objects.get(pk=doc.project_id)
                if project.step < const.PRO_STEP_3:
                    project.step = const.PRO_STEP_3
                    project.save()
                resp = code.get_msg(code.SUCCESS)
            else:
                resp = code.get_msg(code.FLOW_DOC_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_project_docs_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目素材设置详情
def api_project_docs_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = int(request.GET.get("project_id", None))  # 项目ID
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            resp = code.get_msg(code.SUCCESS)
            # 流程
            flow = Flow.objects.filter(pk=obj.flow_id, del_flag=0).first()
            if flow is None:
                resp = code.get_msg(code.FLOW_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            has_jump_project = False
            jump_process = FlowProcess.objects.filter(type=const.PROCESS_JUMP_TYPE,
                                                      del_flag=const.DELETE_FLAG_NO).first()
            if jump_process:
                is_exists = FlowNode.objects.filter(flow_id=flow.pk, process=jump_process,
                                                    del_flag=const.DELETE_FLAG_NO).exists()
                if is_exists:
                    has_jump_project = True
            project = {'id': obj.id, 'name': obj.name, 'level': obj.level, 'type': obj.type, 'purpose': obj.purpose,
                       'flow_id': flow.pk, 'flow_name': flow.name, 'ability_target': obj.ability_target,
                       'has_jump_project': has_jump_project}
            # 项目流程节点
            project_nodes = []
            flow_nodes = FlowNode.objects.filter(flow_id=obj.flow_id, del_flag=0)
            for item in flow_nodes:
                pid = ''
                process_name = ''
                if item.process_id:
                    process = FlowProcess.objects.filter(pk=item.process_id).first()
                    if process:
                        pid = process.pk
                        process_name = process.name

                # 项目角色
                pras = ProjectRoleAllocation.objects.filter(project_id=obj.id,
                                                            node_id=item.id, can_take_in=True)
                project_role_allocs = []
                for ra in pras:
                    doc_ids = ProjectDocRole.objects.filter(project_id=project_id, role_id=ra.role_id, no=ra.no,
                                                            node_id=item.id).values_list('doc_id', flat=True)
                    role = ProjectRole.objects.get(pk=ra.role_id)
                    project_role_allocs.append(
                        {'id': ra.id, 'role_id': role.id, 'no': ra.no, 'name': role.name, 'type': role.type,
                         'doc_ids': list(doc_ids)})
                project_nodes.append(
                    {'id': item.pk, 'name': item.name, 'process_id': pid, 'project_role_allocs': project_role_allocs,
                     'process_name': process_name})
            project_role_type = ProjectRole.objects.filter(project_id=project_id
                                                           ).values_list('type', flat=True).distinct()
            # 项目素材
            project_docs = ProjectDoc.objects.filter(project_id=project_id)
            doc_list = []
            for item in project_docs:
                doc = {
                    'id': item.id, 'name': item.name, 'usage': item.usage, 'file': item.file.url, 'type': item.type,
                    'is_initial': item.is_initial, 'file_type': item.file_type
                }
                doc_list.append(doc)

            resp['d'] = {'project': project, 'project_nodes': project_nodes, 'project_docs': doc_list,
                         'project_role_type': list(project_role_type)}
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_project_docs_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目素材分配
def api_project_docs_allocate(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        data = request.POST.get("data")  # 分配json数据

        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            resp = code.get_msg(code.SUCCESS)
            data = json.loads(data)
            with transaction.atomic():
                # 素材用途更新
                docs_ids = []
                for item in data['project_docs']:
                    docs_ids.append(item['id'])
                    is_initial = False
                    if item['is_initial']:
                        is_initial = True
                    ProjectDoc.objects.filter(pk=item['id']).update(type=item['type'], usage=item['usage'],
                                                                    is_initial=is_initial)

                # 清除原素材分配
                ProjectDocRole.objects.filter(project_id=project_id).delete()
                # ProjectDocRoleNew.objects.filter(project_id=project_id).delete()

                # 保存新分配
                docs_role_list = []
                for item in data['project_docs_roles']:
                    # 更新优化
                    docs_role_list.append(ProjectDocRole(project_id=project_id, node_id=item['node_id'],
                                                         doc_id=item['doc_id'], role_id=item['role_id'], no=item['no']))
                ProjectDocRole.objects.bulk_create(docs_role_list)
                # ProjectDocRoleNew.objects.bulk_create(docs_role_list)
                if obj.step < const.PRO_STEP_3:
                    obj.step = const.PRO_STEP_3
                    obj.save()
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)

        # cache.clear()
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_project_docs_allocate Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目角色设置
def api_project_roles_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.GET.get("project_id", None)  # 项目ID
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            resp = code.get_msg(code.SUCCESS)
            # 流程
            flow = Flow.objects.filter(pk=obj.flow_id, del_flag=0).first()
            if flow is None:
                resp = code.get_msg(code.FLOW_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            has_jump_project = False
            jump_process = FlowProcess.objects.filter(type=const.PROCESS_JUMP_TYPE,
                                                      del_flag=const.DELETE_FLAG_NO).first()
            if jump_process:
                is_exists = FlowNode.objects.filter(flow_id=flow.pk, process=jump_process,
                                                    del_flag=const.DELETE_FLAG_NO).exists()
                if is_exists:
                    has_jump_project = True

            project = {'id': obj.id, 'name': obj.name, 'level': obj.level, 'purpose': obj.purpose,
                       'flow_id': flow.pk, 'flow_name': flow.name, 'type': obj.type,
                       'ability_target': obj.ability_target, 'has_jump_project': has_jump_project}
            # 项目流程节点
            project_nodes = []
            flow_nodes = FlowNode.objects.filter(flow_id=obj.flow_id, del_flag=0)
            for item in flow_nodes:
                is_start_node = FlowTrans.objects.filter(flow_id=flow.id, incoming__startswith='StartEvent',
                                                         outgoing=item.task_id).exists()
                if item.process:
                    process = item.process
                    prc = {
                        'id': process.id, 'name': process.name, 'type': process.type,
                        'file': process.file.url if process.file else None,
                        'image': process.image.url if process.image else None,
                    }
                else:
                    prc = None

                pras = ProjectRoleAllocation.objects.filter(project_id=project_id, node_id=item.id).values()
                look_on = False
                try:
                    projectNodeInfo = item.projectnodeinfo_set.get(project_id=obj.id)
                    look_on = projectNodeInfo.look_on
                except:
                    look_on = False
                project_nodes.append(
                    {'id': item.pk, 'name': item.name, 'process': prc, 'project_role_allocs': list(pras),
                     'look_on': look_on, 'is_start_node': is_start_node})
            # 项目角色，按类型分类
            sql = '''SELECT t.id,t.type,t.`name` role_name,t.max,t.min,t.category,t.image_id,t.capacity, t.job_type_id,i.`name` image_name,i.gender
            from t_project_role t LEFT JOIN t_role_image i ON t.image_id=i.id
            WHERE t.type != \'{0}\' and t.project_id={1}'''.format(const.ROLE_TYPE_OBSERVER, project_id)
            logger.info(sql)
            project_roles = query.select(sql,
                                         ['id', 'type', 'role_name', 'max', 'min', 'category', 'image_id', 'capacity',
                                          'job_type_id',
                                          'image_name', 'gender'])

            # for i in range(0, len(project_roles)):
            #     role_id = project_roles[i]['id']
            #     node_ids = []
            #     if role_id:
            #         node_ids = set(ProjectRoleAllocation.objects.filter(project_id=project_id,
            #                                                             role_id=role_id).values_list('node_id',
            #                                                                                          flat=True))
            #     project_roles[i]['node_ids'] = list(node_ids)
            project_role_type = ProjectRole.objects.filter(project_id=project_id) \
                .exclude(type=const.ROLE_TYPE_OBSERVER).values_list('type', flat=True).distinct()
            logger.info(project_role_type.query)
            # 项目环节角色设置
            project_node_roles = ProjectRoleAllocation.objects.filter(project_id=project_id).values()

            resp['d'] = {'project': project, 'project_nodes': project_nodes, 'project_roles': project_roles,
                         'project_role_type': list(project_role_type), 'project_node_roles': list(project_node_roles)}
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_project_roles_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目角色形象设置
def api_project_role_image_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        role_id = request.POST.get("role_id")  # 项目ID
        image_id = request.POST.get("image_id")  # 项目ID

        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            resp = code.get_msg(code.SUCCESS)
            # 角色形象
            ProjectRole.objects.filter(pk=role_id, project_id=project_id).update(image_id=image_id)
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_project_role_image_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目角色设置
def api_project_roles_configurate(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        data = request.POST.get("data")  # 角色设置数据
        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            projectNodes = json.loads(data)
            with transaction.atomic():
                for key, node in enumerate(projectNodes):
                    projectRoleAllocs = node['project_role_allocs']
                    flowNode = FlowNode.objects.get(pk=node['id'])
                    for key1, pra in enumerate(projectRoleAllocs):
                        ProjectRoleAllocation.objects.filter(pk=pra['id']).update(can_take_in=pra['can_take_in'],
                                                                                  can_start=pra['can_start'],
                                                                                  can_terminate=pra['can_terminate'],
                                                                                  can_brought=pra['can_brought'])
                    projectNodeInfo = ProjectNodeInfo.objects.filter(project=obj, node=flowNode)
                    if projectNodeInfo.count() > 0:
                        projectNodeInfo.update(look_on=node['look_on'])
                    else:
                        ProjectNodeInfo.objects.create(project=obj, node=flowNode, look_on=node['look_on'])
                # 角色形象
                # for item in data['project_roles']:
                #     ProjectRole.objects.filter(pk=item['id']).update(image_id=item['image_id'])

                # # 角色分配，清除原分配，保存新分配
                # ProjectRoleAllocation.objects.filter(project_id=project_id).delete()
                # role_node_list = []
                # for item in data['project_node_roles']:
                #     role_node_list.append(ProjectRoleAllocation(project_id=project_id, node_id=item['node_id'],
                #                                                 role_id=item['role_id'],
                #                                                 can_terminate=item['can_terminate'],
                #                                                 can_brought=item['can_brought'],
                #                                                 num=item['num'], score=item['score']))
                # ProjectRoleAllocation.objects.bulk_create(role_node_list)
                if obj.step < const.PRO_STEP_2:
                    obj.step = const.PRO_STEP_2
                    obj.save()
            resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_project_roles_configurate Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 修改项目
def api_project_update(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("id")  # 项目ID
        name = request.POST.get("name", None)  # 名称
        all_role = request.POST.get("all_role", None)  # 允许一人扮演所有角色
        course = request.POST.get("course", None)  # 课程ID
        reference = request.POST.get("reference", None)  # 成果参考释放方式
        public_status = request.POST.get("public_status", None)  # 申请为公共项目状态
        level = request.POST.get("level", None)  # 实验层次
        entire_graph = request.POST.get("entire_graph", None)  # 流程图完整显示
        can_redo = request.POST.get("can_redo", None)  # 是否允许重做
        is_open = request.POST.get("is_open", None)  # 开放模式
        ability_target = request.POST.get("ability_target", None)  # 能力目标
        start_time = request.POST.get("start_time", None)  # 开放开始时间
        end_time = request.POST.get("end_time", None)  # 开放结束时间
        intro = request.POST.get("intro", None)  # 项目简介
        purpose = request.POST.get("purpose", None)  # 实验目的
        requirement = request.POST.get("requirement", None)  # 实验要求
        use_to = request.POST.get("use_to", None)

        # 课程没有就保存
        Course.objects.get_or_create(name=course)

        obj = Project.objects.filter(id=project_id, del_flag=0).first()
        if obj:
            if all([name, all_role, course, reference, public_status, level, entire_graph, can_redo,
                    is_open, ability_target, intro, purpose, requirement]):
                if len(name) == 0 or len(name) > 60:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                if len(course) == 0 or len(course) > 45:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                if is_open == '3':
                    if start_time is None or start_time == '' or end_time is None or end_time == '':
                        resp = code.get_msg(code.PARAMETER_ERROR)
                        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
                    start_time = datetime.strptime(start_time, '%Y-%m-%d')
                    end_time = datetime.strptime(end_time, '%Y-%m-%d')
                else:
                    start_time = None
                    end_time = None

                if is_open == '4':
                    target_users = eval(request.POST.get("target_users", ''))
                    obj.target_users = Tuser.objects.filter(id__in=target_users)
                if is_open == '5':
                    target_parts = request.POST.get("target_parts", None)
                    obj.target_parts_id = target_parts

                obj.name = name
                obj.all_role = all_role
                obj.course = TCourse.objects.get(id=course)
                obj.reference = reference
                obj.public_status = public_status
                obj.level = level
                obj.entire_graph = entire_graph
                obj.can_redo = can_redo
                obj.is_open = is_open
                obj.ability_target = ability_target
                obj.start_time = start_time
                obj.end_time = end_time
                obj.intro = intro
                obj.purpose = purpose
                obj.requirement = requirement
                obj.use_to_id = use_to
                if obj.step < const.PRO_STEP_1:
                    obj.step = const.PRO_STEP_1
                obj.save()
                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {'results': 'success'}
                cache.clear()

            else:
                resp = code.get_msg(code.PARAMETER_ERROR)
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)

    except Exception as e:
        logger.exception('api_project_update Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询项目相关实验数据
def api_project_has_experiment(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.GET.get("project_id", None)  # 项目ID
        exists = Experiment.objects.filter(pk=project_id, del_flag=0).exists()
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {
            'project_id': project_id, 'has_experiment': exists
        }
    except Exception as e:
        logger.exception('api_project_experiment Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 删除项目
def api_project_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id", None)  # 项目ID
        if project_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            cache.clear()

            with transaction.atomic():
                obj.del_flag = 1
                obj.save()
                # todo 删除相关实验任务，包括跳转实验
                Experiment.objects.filter(project_id=project_id).update(del_flag=1)
                ProjectRole.objects.filter(project_id=project_id).delete()
                ProjectDocRole.objects.filter(project_id=project_id).delete()
                # ProjectDocRoleNew.objects.filter(project_id=project_id).delete()
                ProjectRoleAllocation.objects.filter(project_id=project_id).delete()
                project_ids = ProjectJump.objects.filter(jump_project_id=project_id).values_list('project_id',
                                                                                                 flat=True)
                Experiment.objects.filter(project_id__in=project_ids).update(del_flag=1)
                ProjectJump.objects.filter(jump_project_id=project_id).delete()
                Project.objects.filter(id=project_id).delete()

                # 三期 - 如果一个课程下面的项目全部删除了，同时删除课程
                project_list = Project.objects.filter(course=obj.course, del_flag=0)
                if not project_list:
                    cc = Course.objects.filter(name=obj.course)
                    cc.delete()

                resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_project_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目详情
def api_project_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        project_id = request.GET.get("project_id", None)  # 项目ID

        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            flow = Flow.objects.get(pk=obj.flow_id)
            # 项目角色
            sql = '''SELECT t.id,t.type,t.`name` role_name,t.max,t.min,t.category,t.image_id,
            i.`name` image_name, concat('/media/', i.`avatar`) image_url
            from t_project_role t LEFT JOIN t_role_image i ON t.image_id=i.id
            WHERE t.type != \'''' + const.ROLE_TYPE_OBSERVER + '''\' and t.project_id={0}'''.format(project_id)
            project_roles = query.select(sql, ['id', 'type', 'role_name', 'max', 'min', 'category', 'image_id',
                                               'image_name', 'image_url'])
            # 项目素材
            project_docs = ProjectDoc.objects.filter(project_id=project_id)
            doc_list = []
            for item in project_docs:
                doc = {
                    'id': item.id, 'name': item.name, 'usage': item.usage, 'type': item.type,
                    'file': item.file.url if item.file else '',
                    'content': item.content, 'is_initial': item.is_initial, 'file_type': item.file_type
                }
                doc_list.append(doc)
            resp = code.get_msg(code.SUCCESS)
            start_time = obj.start_time.strftime('%Y-%m-%d') if obj.start_time else ''
            end_time = obj.end_time.strftime('%Y-%m-%d') if obj.end_time else ''
            # 项目信息
            has_jump_project = False
            jump_process = FlowProcess.objects.filter(type=const.PROCESS_JUMP_TYPE,
                                                      del_flag=const.DELETE_FLAG_NO).first()
            if jump_process:
                is_exists = FlowNode.objects.filter(flow_id=flow.pk, process=jump_process,
                                                    del_flag=const.DELETE_FLAG_NO).exists()
                if is_exists:
                    has_jump_project = True
            resp['d'] = {
                'flow_id': obj.flow_id, 'flow_name': flow.name, 'name': obj.name,
                'all_role': obj.all_role, 'course': obj.course,
                'reference': obj.reference, 'public_status': obj.public_status, 'level': obj.level,
                'entire_graph': obj.entire_graph, 'can_redo': obj.can_redo, 'is_open': obj.is_open,
                'ability_target': obj.ability_target, 'start_time': start_time, 'has_jump_project': has_jump_project,
                'end_time': end_time, 'intro': obj.intro, 'purpose': obj.purpose,
                'requirement': obj.requirement, 'id': obj.id, 'type': obj.type, 'flow_xml': flow.xml,
                'step': obj.step, 'roles': project_roles, 'docs': doc_list
            }
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_project_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 创建项目
def api_project_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if not permission_check(request, 'code_create_project'):
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        flow_id = request.POST.get("flow_id", None)  # 流程ID
        name = request.POST.get("name", None)  # 名称
        all_role = request.POST.get("all_role", None)  # 允许一人扮演所有角色
        course = request.POST.get("course", None)  # 课程ID
        reference = request.POST.get("reference", None)  # 成果参考释放方式
        public_status = request.POST.get("public_status", None)  # 申请为公共项目状态
        level = request.POST.get("level", None)  # 实验层次
        entire_graph = request.POST.get("entire_graph", None)  # 流程图完整显示
        can_redo = request.POST.get("can_redo", None)  # 是否允许重做
        is_open = request.POST.get("is_open", None)  # 开放模式
        ability_target = request.POST.get("ability_target", None)  # 能力目标
        start_time = request.POST.get("start_time", None)  # 开放开始时间
        end_time = request.POST.get("end_time", None)  # 开放结束时间
        intro = request.POST.get("intro", None)  # 项目简介
        purpose = request.POST.get("purpose", None)  # 实验目的
        requirement = request.POST.get("requirement", None)  # 实验要求
        officeItem = request.POST.get("officeItem", None)
        use_to = request.POST.get("use_to", None)
        logger.info('-----api_project_create----')

        if all([flow_id, name, all_role, course, reference, public_status, level, entire_graph, can_redo,
                is_open, ability_target, intro, purpose, requirement, officeItem]):
            name = name.strip()
            if len(name) == 0 or len(name) > 32:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if len(course) == 0 or len(course) > 45:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            if is_open == '3' and (start_time is None or start_time is None):
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 开始模式是自由的话，不需要传 start_time 和 end_time
            if is_open == '3':
                if start_time is None or start_time == '':
                    start_time = None
                else:
                    start_time = datetime.strptime(start_time, '%Y-%m-%d')
                if end_time is None or end_time == '':
                    end_time = None
                else:
                    end_time = datetime.strptime(end_time, '%Y-%m-%d')
            else:
                start_time = None
                end_time = None

            if start_time and end_time:
                if end_time < start_time:
                    resp = code.get_msg(code.PARAMETER_ERROR)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            flow = Flow.objects.filter(pk=flow_id).first()
            if flow is None:
                resp = code.get_msg(code.FLOW_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 验证名称
            exists = Project.objects.filter(name=name, del_flag=0).exists()
            if exists:
                resp = code.get_msg(code.PROJECT_NAME_HAS_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 判断流程是否有角色设置
            roles = FlowRole.objects.filter(flow_id=flow_id, del_flag=0)
            if roles.exists() is False:
                resp = code.get_msg(code.FLOW_ROLE_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            # 课程没有就保存
            # Course.objects.get_or_create(name=course)
            with transaction.atomic():
                obj = Project.objects.create(
                    flow_id=flow_id, name=name, all_role=all_role, course=TCourse.objects.get(id=course),
                    reference=reference, public_status=public_status, level=level, officeItem_id=officeItem,
                    entire_graph=entire_graph, can_redo=can_redo, is_open=is_open,
                    ability_target=ability_target, start_time=start_time, end_time=end_time,
                    intro=intro, purpose=purpose, requirement=requirement,
                    type=flow.type_label, created_by=Tuser.objects.get(id=request.user.pk),
                    created_role_id=request.session['login_type'], use_to_id=use_to
                )

                if is_open == '4':
                    target_users = eval(request.POST.get("target_users", ''))
                    obj.target_users.add(*Tuser.objects.filter(id__in=target_users))
                if is_open == '5':
                    target_parts = request.POST.get("target_parts", None)
                    Project.objects.filter(pk=obj.pk).update(target_parts_id=target_parts)

                # 复制流程角
                project_roles = []
                for item in roles:
                    project_roles.append(ProjectRole(project_id=obj.pk, image_id=item.image_id, name=item.name,
                                                     type=item.type, min=item.min, max=item.max, flow_role_id=item.id,
                                                     category=item.category, capacity=item.capacity,
                                                     job_type=item.job_type))
                ProjectRole.objects.bulk_create(project_roles)
                logger.info('-----bulk_create project_roles:%s done----' % len(project_roles))

                # 复制流程角色分配设置
                project_allocations = []
                allocations = FlowRoleAllocation.objects.filter(flow_id=flow_id, del_flag=0)
                for item in allocations:
                    # 将角色分配中的role_id设置为ProjectRole id
                    role = ProjectRole.objects.filter(project_id=obj.pk, flow_role_id=item.role_id).first()
                    if role:
                        project_allocations.append(ProjectRoleAllocation(project_id=obj.pk, node_id=item.node_id,
                                                                         role_id=role.id,
                                                                         can_start=item.can_start,
                                                                         can_terminate=item.can_terminate,
                                                                         can_brought=item.can_brought,
                                                                         can_take_in=item.can_take_in,
                                                                         no=item.no))
                ProjectRoleAllocation.objects.bulk_create(project_allocations)
                logger.info('-----bulk_create project_allocations:%s----' % len(project_allocations))

                # 复制流程素材设置
                docs_allocations = []
                docs = FlowDocs.objects.filter(flow_id=flow_id, del_flag=0)
                for item in docs:
                    flow_node_docs = FlowNodeDocs.objects.filter(flow_id=flow_id, doc_id=item.id, del_flag=0)
                    if flow_node_docs.exists():  # doc에 해당하는 flow_node가 존재
                        new = ProjectDoc.objects.create(project_id=obj.pk, name=item.name, type=item.type,
                                                        usage=item.usage, file=item.file, content=item.content,
                                                        file_type=item.file_type,
                                                        is_flow=True)  # flowDoc를 projectDoc에 복사
                        for n in flow_node_docs:  # doc에 해당하는 flow_node들을 돌려주면서
                            projectRoleAllocations = ProjectRoleAllocation.objects.filter(project_id=obj.pk,
                                                                                          node_id=n.node_id,
                                                                                          can_take_in=True)  # 해당한 node에 참가하는 role들을 얻기
                            for r in projectRoleAllocations:  # 해당한 node에 참가하는 role들을 no함께 돌려준다
                                docs_allocations.append(
                                    ProjectDocRole(project_id=obj.pk, node_id=n.node_id, doc_id=new.pk,
                                                   role_id=r.role_id, no=r.no))
                ProjectDocRole.objects.bulk_create(docs_allocations)
                logger.info('-----bulk_create docs_allocations:%s----' % len(docs_allocations))

                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {'id': obj.id}
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
    except Exception as e:
        logger.exception('api_project_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目列表
def api_project_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.GET.get("search", None)  # 搜索关键字
        page = int(request.GET.get("page", 1))  # 页码
        size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

        qs = Project.objects.filter(del_flag=0)

        if search:
            qs = qs.filter(name__icontains=search)

        user = request.user

        if request.session['login_type'] != 1:
            if request.session['login_type'] in [2, 6]:
                groupInfo = json.loads(public_fun.getGroupByGroupManagerID(request.session['login_type'], user.id))
                group = AllGroups.objects.get(id=groupInfo['group_id'])
                createdByGMs = [manager.id for manager in group.groupManagers.all()]  # get all group managers
                createdByGMAs = [manager.id for manager in group.groupManagerAssistants.all()]  # get all group manager assistants
                companies = group.tcompany_set.all()  # get all companies
                createdByCMs = []
                createdByCMAs = []
                for company in companies:
                    companyManagers = company.tcompanymanagers_set.all()  # get all company managers
                    companyAssistants = company.assistants.all()  # get all company manager assistants
                    for companyManager in companyManagers:
                        createdByCMs.append(companyManager.tuser.id)
                    for companyAssistant in companyAssistants:
                        createdByCMAs.append(companyAssistant.id)
                qs = qs.filter(
                    Q(is_group_share=1) |
                    ((Q(created_by__in=createdByGMs) & Q(created_role_id=2)) |
                     (Q(created_by__in=createdByGMAs) & Q(created_role_id=6)) |
                     (Q(created_by__in=createdByCMs) & Q(created_role_id=3)) |
                     (Q(created_by__in=createdByCMAs) & Q(created_role_id=7)))
                )

            if request.session['login_type'] in [3, 7]:
                groupInfo = json.loads(public_fun.getGroupByCompanyManagerID(request.session['login_type'], user.id))
                groupID = groupInfo['group_id']
                group = AllGroups.objects.get(pk=int(groupID))
                createdByCMs = []
                createdByCMAs = []
                companies = group.tcompany_set.all()  # get all companies
                for company in companies:
                    companyManagers = company.tcompanymanagers_set.all()  # get all company managers
                    companyAssistants = company.assistants.all()  # get all company manager assistants
                    for companyManager in companyManagers:
                        createdByCMs.append(companyManager.tuser.id)
                    for companyAssistant in companyAssistants:
                        createdByCMAs.append(companyAssistant.id)
                qs = qs.filter(
                    (Q(created_by=user.id) & Q(created_role_id=request.session['login_type'])) |
                    ((Q(created_by__in=createdByCMs) & Q(created_role_id=3) & Q(is_company_share=1)) |
                     (Q(created_by__in=createdByCMAs) & Q(created_role_id=7) & Q(is_company_share=1)))
                )
            if request.session['login_type'] == 5:
                group_id = request.GET.get("group_id", None)
                company_id = request.GET.get("company_id", None)
                office_id = request.GET.get('office_id', None)
                by_method = request.GET.get('by_method', None)
                if group_id and by_method == 'company':
                    group = AllGroups.objects.get(pk=int(group_id))
                    groupManagers = group.groupManagers.all()
                    groupAssistants = group.groupManagerAssistants.all()
                    createdByGMs = [manager.id for manager in groupManagers]
                    createdByGMAs = [manager.id for manager in groupAssistants]
                    companies = group.tcompany_set.all()  # get all companies
                    createdByCMs = []
                    createdByCMAs = []
                    for company in companies:
                        companyManagers = company.tcompanymanagers_set.all()  # get all company managers
                        companyAssistants = company.assistants.all()  # get all company manager assistants
                        for companyManager in companyManagers:
                            createdByCMs.append(companyManager.tuser.id)
                        for companyAssistant in companyAssistants:
                            createdByCMAs.append(companyAssistant.id)
                    qs = qs.filter(
                        (Q(created_by__in=createdByGMs) & Q(created_role_id=2)) |
                        (Q(created_by__in=createdByGMAs) & Q(created_role_id=6)) |
                        (Q(created_by__in=createdByCMs) & Q(created_role_id=3)) |
                        (Q(created_by__in=createdByCMAs) & Q(created_role_id=7))
                    )
                if company_id and by_method == 'company':
                    company = TCompany.objects.get(pk=int(company_id))
                    companyManagers = company.tcompanymanagers_set.all()
                    companyAssistants = company.assistants.all()
                    createdByCMs = []
                    createdByCMAs = []
                    for companyManager in companyManagers:
                        createdByCMs.append(companyManager.tuser.id)
                    for companyAssistant in companyAssistants:
                        createdByCMAs.append(companyAssistant.id)
                    qs = qs.filter(
                        (Q(created_by__in=createdByCMs) & Q(created_role_id=3)) |
                        (Q(created_by__in=createdByCMAs) & Q(created_role_id=7))
                    )
                if office_id and by_method == 'office':
                    qs = qs.filter(officeItem_id=int(office_id))
                today = datetime.today()
                if user.tposition and user.tposition.parts:
                    query = Q(is_open=1) | (Q(is_open=3) & Q(start_time__lte=today) & Q(end_time__gte=today)) | (Q(is_open=4) & Q(target_users__in=[user])) | (Q(is_open=5) & Q(target_parts=user.tposition.parts))
                else:
                    query = Q(is_open=1) | (Q(is_open=3) & Q(start_time__lte=today) & Q(end_time__gte=today)) | (Q(is_open=4) & Q(target_users__in=[user]))
                qs = qs.exclude(Q(is_open=2)).filter(query)

        qs = qs.filter(del_flag=0)
        paginator = Paginator(qs, size)

        try:
            projects = paginator.page(page)
        except EmptyPage:
            projects = paginator.page(1)

        results = []
        for project in projects:
            shareAble = 0
            editAble = 0
            deleteAble = 0
            currentShare = 0
            start_time = project.start_time.strftime('%Y-%m-%d') if project.start_time else ''
            end_time = project.end_time.strftime('%Y-%m-%d') if project.end_time else ''
            flow = Flow.objects.filter(pk=project.flow_id, del_flag=0).first()
            flow_data = None
            if flow:
                flow_data = {'name': flow.name, 'xml': flow.xml}

            if request.session['login_type'] == 1:
                shareAble = 1
                editAble = 1
                deleteAble = 1
            else:
                if project.created_by.id == user.id and project.created_role_id == request.session['login_type']:
                    shareAble = 1
                    editAble = 1
                    deleteAble = 1
                if project.created_by.id == user.id:
                    if request.session['login_type'] == 2:
                        if project.is_group_share == 1:
                            currentShare = 1
                if project.created_by.id == user.id:
                    if request.session['login_type'] == 3:
                        if project.is_company_share == 1:
                            currentShare = 1
            company_name = project.created_by.tcompanymanagers_set.get().tcompany.name if project.created_role_id == 3 else project.created_by.t_company_set_assistants.get().name if project.created_role_id == 7 else ''

            results.append({
                'id': project.id, 'flow_id': project.flow_id, 'name': project.name, 'all_role': project.all_role,
                'company_name': company_name,
                'officeItem_name': project.officeItem.name if project.officeItem else None,
                'course': project.course_id,
                'target_users': [{'id': item.id, 'text': item.username} for item in project.target_users.all()],
                'course_name': project.course.name, 'reference': project.reference,
                'public_status': project.public_status, 'level': project.level,
                'entire_graph': project.entire_graph, 'type': project.type, 'can_redo': project.can_redo,
                'is_open': project.is_open,
                'ability_target': project.ability_target, 'start_time': start_time, 'end_time': end_time,
                'created_by': user_simple_info(project.created_by.id),
                'created_role': project.created_role_id,
                'create_time': project.create_time is not None and project.create_time.strftime('%Y-%m-%d') or '',
                'flow': flow_data, 'intro': project.intro,
                'purpose': project.purpose, 'requirement': project.requirement, 'protected': project.protected,
                'is_group_share': project.is_group_share,
                'is_company_share': project.is_company_share, 'share_able': shareAble, 'edit_able': editAble,
                'delete_able': deleteAble, 'current_share': currentShare,
                'target_parts': {'value': project.target_parts.id, 'text': project.target_parts.name} if project.target_parts_id else {},
                'use_to': {'value': project.use_to.id, 'text': project.use_to.name} if project.use_to else {}
            })

        # 分页信息
        paging = {
            'count': paginator.count,
            'has_previous': projects.has_previous(),
            'has_next': projects.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': projects.number,
            'page_size': size
        }
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_project_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 复制项目
def api_project_copy(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id", None)  # 流程ID
        name = request.POST.get("name", None)
        logger.info('project_id:%s,name:%s' % (project_id, name))
        if project_id and name:
            name = name.strip()
            if len(name) == 0 or len(name) > 32:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            project = Project.objects.filter(pk=project_id, del_flag=0).first()
            if project:
                # 验证名称
                exists = Project.objects.filter(name=name, del_flag=0).exclude(pk=project_id).exists()
                if exists:
                    resp = code.get_msg(code.PROJECT_NAME_HAS_EXIST)
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                flow = Flow.objects.filter(pk=project.flow_id).first()

                with transaction.atomic():
                    obj = Project.objects.create(flow_id=project.flow_id, name=name, all_role=project.all_role,
                                                 course=project.course, reference=project.reference,
                                                 public_status=project.public_status, level=project.level,
                                                 entire_graph=project.entire_graph, type=project.type,
                                                 can_redo=project.can_redo, is_open=project.is_open,
                                                 ability_target=project.ability_target,
                                                 start_time=project.start_time, end_time=project.end_time,
                                                 intro=project.intro, purpose=project.purpose,
                                                 requirement=project.requirement, step=project.step,
                                                 created_by=request.user.pk)
                    # 复制流程角色设置
                    role_map = []
                    roles = ProjectRole.objects.filter(project_id=project_id)
                    for item in roles:
                        new = ProjectRole.objects.create(project_id=obj.pk, image_id=item.image_id, name=item.name,
                                                         type=item.type, min=item.min, max=item.max,
                                                         category=item.category, flow_role_id=item.flow_role_id)
                        role_map.append((item.id, new.id))

                    project_allocations = []
                    allocations = ProjectRoleAllocation.objects.filter(project_id=project_id)
                    for item in allocations:
                        new_role_id = public_fun.get_map(role_map, item.role_id)
                        if new_role_id is None:
                            continue
                        project_allocations.append(ProjectRoleAllocation(project_id=obj.pk, node_id=item.node_id,
                                                                         role_id=new_role_id,
                                                                         can_start=item.can_start,
                                                                         can_terminate=item.can_terminate,
                                                                         can_brought=item.can_brought,
                                                                         num=item.num, score=item.score))
                    ProjectRoleAllocation.objects.bulk_create(project_allocations)

                    # 复制流程素材设置
                    docs_map = []
                    docs = ProjectDoc.objects.filter(project_id=project_id)
                    for item in docs:
                        new = ProjectDoc.objects.create(project_id=obj.pk, name=item.name, type=item.type,
                                                        usage=item.usage, file=item.file, file_type=item.file_type,
                                                        content=item.content,
                                                        is_initial=item.is_initial, is_flow=item.is_flow)
                        docs_map.append((item.id, new.id))

                    project_docs_role = []
                    docs_roles = ProjectDocRole.objects.filter(project_id=project_id)
                    for item in docs_roles:
                        new_doc_id = public_fun.get_map(docs_map, item.doc_id)
                        new_role_id = public_fun.get_map(role_map, item.role_id)
                        if new_doc_id is None or new_role_id is None:
                            continue
                        project_docs_role.append(ProjectDocRole(project_id=obj.pk, node_id=item.node_id,
                                                                doc_id=new_doc_id, role_id=new_role_id))
                    ProjectDocRole.objects.bulk_create(project_docs_role)

                    project_jumps = []
                    jumps = ProjectJump.objects.filter(project_id=project_id)
                    for item in jumps:
                        project_jumps.append(ProjectJump(project_id=obj.pk, node_id=item.node_id,
                                                         jump_project_id=item.jump_project_id))
                    if project_jumps:
                        ProjectJump.objects.bulk_create(project_jumps)

                    resp = code.get_msg(code.SUCCESS)
                    start_time = obj.start_time.strftime('%Y-%m-%d') if obj.start_time else ''
                    end_time = obj.end_time.strftime('%Y-%m-%d') if obj.end_time else ''
                    resp['d'] = {
                        'flow_id': obj.flow_id, 'name': obj.name, 'all_role': obj.all_role, 'course': obj.course,
                        'reference': obj.reference, 'public_status': obj.public_status, 'level': obj.level,
                        'entire_graph': obj.entire_graph, 'type': obj.type, 'can_redo': obj.can_redo,
                        'is_open': obj.is_open, 'ability_target': obj.ability_target,
                        'start_time': start_time, 'end_time': end_time, 'flow': {'name': flow.name},
                        'created_by': user_simple_info(obj.created_by),
                        'create_time': project.create_time.strftime('%Y-%m-%d'),
                        'intro': obj.intro, 'purpose': obj.purpose, 'requirement': obj.requirement, 'id': obj.id
                    }
            else:
                resp = code.get_msg(code.PROJECT_NOT_EXIST)
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)

    except Exception as e:
        logger.exception('api_project_copy Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 查询和项目相关的实验
def api_project_related(request):
    resp = auth_check(request, 'GET')
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.GET.get('project_id', None)
        if project_id is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        project = Project.objects.filter(pk=project_id).first()
        if project:
            experiments = Experiment.objects.filter(project_id=project_id, del_flag=0)
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
            # 跳转项目相关实验
            project_ids = ProjectJump.objects.filter(jump_project_id=project_id).values_list('project_id',
                                                                                             flat=True)
            jump_experiments = Experiment.objects.filter(project_id__in=project_ids, del_flag=0)
            for exp in jump_experiments:
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

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'experiments': experiment_list, 'id': project.id, 'name': project.name, 'level': project.level,
                'ability_tartget': project.ability_target, 'exp_count': experiments.count(), 'type': project.type
            }
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_project_related Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目跳转设置
def api_project_jump_detail(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.GET.get("project_id", None)  # 项目ID
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            resp = code.get_msg(code.SUCCESS)
            # 流程
            flow = Flow.objects.filter(pk=obj.flow_id, del_flag=0).first()
            if flow is None:
                resp = code.get_msg(code.FLOW_NOT_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            has_jump_project = False
            jump_process = FlowProcess.objects.filter(type=const.PROCESS_JUMP_TYPE,
                                                      del_flag=const.DELETE_FLAG_NO).first()
            if jump_process:
                is_exists = FlowNode.objects.filter(flow_id=flow.pk, process=jump_process,
                                                    del_flag=const.DELETE_FLAG_NO).exists()
                if is_exists:
                    has_jump_project = True

            project = {'id': obj.id, 'name': obj.name, 'level': obj.level, 'purpose': obj.purpose,
                       'flow_id': flow.pk, 'flow_name': flow.name, 'type': obj.type,
                       'ability_target': obj.ability_target, 'has_jump_project': has_jump_project}
            # 项目流程节点
            project_nodes = []
            flow_nodes = FlowNode.objects.filter(flow_id=obj.flow_id, del_flag=0)
            for item in flow_nodes:
                if item.process:
                    process = item.process
                    prc = {
                        'id': process.id, 'name': process.name, 'type': process.type,
                        'file': process.file.url if process.file else None,
                        'image': process.image.url if process.image else None,
                    }
                else:
                    prc = None

                project_jump = None
                jump = ProjectJump.objects.filter(project_id=project_id, node_id=item.pk).first()
                if jump:
                    p = Project.objects.filter(pk=jump.jump_project_id, del_flag=0).first()
                    if p:
                        project_jump = {'id': jump.jump_project_id, 'name': p.name}

                project_nodes.append({'id': item.pk, 'name': item.name, 'process': prc, 'project_jump': project_jump})

            resp['d'] = {'project': project, 'project_nodes': project_nodes}
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
    except Exception as e:
        logger.exception('api_project_jump_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目跳转设置
def api_project_jump_setup(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id")  # 项目ID
        data = request.POST.get("data")  # 分配json数据
        logger.info(data)

        if data is None:
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        obj = Project.objects.filter(pk=project_id, del_flag=0).first()
        if obj:
            # 如已创建实验，不能修改
            is_exists = Experiment.objects.filter(project_id=project_id, del_flag=0).exists()
            if is_exists:
                resp = code.get_msg(code.PROJECT_JUMP_HAS_USE)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            cache.clear()

            resp = code.get_msg(code.SUCCESS)
            data = json.loads(data)
            with transaction.atomic():
                # 保存新分配
                jump_list = []
                for item in data['project_jumps']:
                    if project_id == item['jump_project_id']:
                        resp = code.get_msg(code.PROJECT_JUMP_CANNOT_SETUP_SELF)
                        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

                    jump_list.append(ProjectJump(project_id=project_id, node_id=item['node_id'],
                                                 jump_project_id=item['jump_project_id']))

                # 清除原分配
                ProjectJump.objects.filter(project_id=project_id).delete()
                ProjectJump.objects.bulk_create(jump_list)
                if obj.step < const.PRO_STEP_4:
                    obj.step = const.PRO_STEP_4
                    obj.save()
        else:
            resp = code.get_msg(code.PROJECT_NOT_EXIST)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_project_jump_setup Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 项目设置保护/解除保护
def api_project_protected(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        project_id = request.POST.get("project_id", None)  # 项目 ID

        project = Project.objects.get(pk=project_id)

        # 环节保护状态取反
        if project.protected == 1:
            project.protected = 0
        else:
            project.protected = 1

        project.save()

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('api_project_protected Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# 三期 - 共享
def api_project_share(request):
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

        # Group Manager
        if request.session['login_type'] == 2:
            ids = [i for i in ids_set]
            print ids
            Project.objects.filter(id__in=ids).update(is_group_share=1)
        if request.session['login_type'] == 3:
            ids = [i for i in ids_set]
            Project.objects.filter(id__in=ids).update(is_company_share=1)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_project_unshare(request):
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

        # Group Manager
        if request.session['login_type'] == 2:
            ids = [i for i in ids_set]
            Project.objects.filter(id__in=ids).update(is_group_share=0)
        if request.session['login_type'] == 3:
            ids = [i for i in ids_set]
            Project.objects.filter(id__in=ids).update(is_company_share=0)

        resp = code.get_msg(code.SUCCESS)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_allusers_allparts(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        users = [{'id': item.id, 'text': item.username} for item in Tuser.objects.filter(roles=5)]
        parts = [{'value': item.id, 'text': item.company.name + ' : ' + item.name} for item in TParts.objects.all()]
        use_to = []
        # if login_type in [2, 6]:
        #     group_id = request.user.allgroups_set.get().id if login_type == 2 else request.user.allgroups_set_assistants.get().id
        #     use_to = [{'value': item.id, 'text': item.company.name + ' : ' + item.name} for item in TParts.objects.filter(company__group=group_id)]
        if login_type in [3, 7]:
            company_id = request.user.tcompanymanagers_set.get().tcompany.id if login_type == 3 else request.user.t_company_set_assistants.get().id
            use_to = [{'value': item.id, 'text': item.name} for item in TParts.objects.filter(company_id=company_id)]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'users': users, 'parts': parts, 'use_to_list': use_to}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_allusers_allparts Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
