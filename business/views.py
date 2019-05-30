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
from experiment.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation
from workflow.service import get_start_node, bpmn_color
from datetime import datetime


# Get No-Deleted Experiments
def api_experiment_list_nodel(request):
    if request.session['login_type'] in [2, 6]:
        resp = auth_check(request, "GET")
        if resp != {}:
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        try:
            userID = request.user.id
            search = request.GET.get("search", None)  # 关键字
            page = int(request.GET.get("page", 1))  # 页码
            size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

            qs = Experiment.objects.filter(del_flag=0)

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
                    'id': item.id, 'name':item.name, 'show_nickname': item.show_nickname,
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
            search = request.GET.get("search", None)  # 关键字
            page = int(request.GET.get("page", 1))  # 页码
            size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

            qs = Experiment.objects.filter(del_flag=1)

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
                          'team_name': team.name, 'members': member_list, 'teacher': course_class.teacher1.name if course_class else None,
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