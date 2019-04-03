# -*- coding: utf-8 -*-

from experiment.models import *
from workflow.models import *
from project.models import *
import json


# LETS1升级2
# def lets2_update():
#     # 实验
#     exps = Experiment.objects.filter(del_flag=0)
#     total = exps.count()
#     i = 1
#     for e in exps:
#         e.cur_project_id = e.project_id
#         e.save()
#         MemberRole.objects.filter(experiment_id=e.pk).update(project_id=e.project_id)
#         ExperimentTransPath.objects.filter(experiment_id=e.pk).update(project_id=e.project_id)
#         print '%d/%d' % (i, total)
#         i += 1

#
# def lets2_action_setup():
#     # 配置数据迁移
#     flows = Flow.objects.filter(del_flag=0)
#     total = flows.count()
#     lst = []
#     i = 1
#     for f in flows:
#         flow_role_allocation = FlowRoleAllocation.objects.filter(flow_id=f.pk, del_flag=0)
#         for item in flow_role_allocation:
#             ids = []
#             # 流程环节角色动作
#             flow_action_ids = FlowRoleAction.objects.filter(flow_id=f.pk, node_id=item.node_id,
#                                                             role_id=item.role_id,
#                                                             del_flag=0).values_list('action_id', flat=True)
#             for d in flow_action_ids:
#                 ids.append(int(d))
#
#             # print ids
#             lst.append(FlowRoleActionNew(flow_id=f.pk, node_id=item.node_id, role_id=item.role_id,
#                                          actions=ids))
#
#         print '%d/%d' % (i, total)
#         i += 1
#     FlowRoleActionNew.objects.bulk_create(lst)
#
#
# def lets2_process_setup():
#     # 配置数据迁移
#     flows = Flow.objects.filter(del_flag=0)
#     total = flows.count()
#     lst = []
#     i = 1
#     for f in flows:
#         flow_role_allocation = FlowRoleAllocation.objects.filter(flow_id=f.pk, del_flag=0)
#         for item in flow_role_allocation:
#             ids = []
#             # 流程环节角色动作
#             action_ids = ProcessRoleAction.objects.filter(flow_id=f.pk, node_id=item.node_id,
#                                                           role_id=item.role_id,
#                                                           del_flag=0).values_list('action_id', flat=True)
#             for d in action_ids:
#                 ids.append(int(d))
#
#             # print ids
#             lst.append(ProcessRoleActionNew(flow_id=f.pk, node_id=item.node_id, role_id=item.role_id,
#                                             actions=ids))
#         print '%d/%d' % (i, total)
#         i += 1
#     ProcessRoleActionNew.objects.bulk_create(lst)


# def lets2_process_check():
#     # 配置数据迁移
#     nodes = FlowNode.objects.filter(del_flag=0)
#     total = nodes.count()
#     lst = []
#     i = 1
#     for node in nodes:
#         if node.process:
#             process = node.process
#             if process.type == 1:
#                 role_actions = ProcessRoleActionNew.objects.filter(flow_id=node.flow_id, node_id=node.pk, del_flag=0).first()
#                 if role_actions:
#                     btns = json.loads(role_actions.actions)
#                     for id in btns:
#                         action = ProcessAction.objects.filter(pk=id, del_flag=0).first()
#                         if action.process_id != process.pk:
#                             lst.append(node.pk)
#                             break
#
#             print '%d/%d' % (i, total)
#             i += 1
#     print lst


def lets2_project_doc_mv():
    # 配置数据迁移
    projects = Project.objects.filter(del_flag=0)
    total = projects.count()
    lst = []
    i = 1
    for p in projects:
        role_allocation = ProjectRoleAllocation.objects.filter(project_id=p.pk)
        for item in role_allocation:
            ids = []
            # 流程环节角色动作
            obj_ids = ProjectDocRole.objects.filter(project_id=p.pk, node_id=item.node_id,
                                                    role_id=item.role_id).values_list('doc_id', flat=True)
            for d in obj_ids:
                ids.append(int(d))

            # print ids
            lst.append(ProjectDocRoleNew(project_id=p.pk, node_id=item.node_id, role_id=item.role_id, docs=ids))
        print '%d/%d' % (i, total)
        i += 1
    ProjectDocRoleNew.objects.bulk_create(lst)
