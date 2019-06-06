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

logger = logging.getLogger(__name__)

# def get_role_allocs_status_by_user(business, path, user):
#     role_alloc_list = []
#     qs = BusinessRoleAllocationStatus.objects.filter(business=business, path=path, business_role_allocation__node=path.node, user=user)
#     for role_alloc_status in qs:
#         business_role_alloc = role_alloc_status.business_role_allocation
#     role_list = query.select(sql, ['id', 'come_status', 'sitting_status', 'stand_status',
#                                    'vote_status', 'show_status', 'speak_times', 'name', 'avatar'])
#     for i in range(0, len(role_list)):
#         role_perm = ProjectRoleAllocation.objects.filter(project_id=exp.cur_project_id, node_id=path.node_id,
#                                                          role_id=role_list[i]['id']).first()
#         can_terminate = False
#         can_edit = False
#         if role_perm:
#             can_edit = True
#             can_terminate = role_perm.can_terminate
#
#         role_list[i]['can_terminate'] = can_terminate
#         role_list[i]['can_edit'] = can_edit
#         role_list[i]['avatar'] = '/media/%s' % role_list[i]['avatar']
#         role_list[i]['code_position'] = ''
#         if path.control_status != 2:
#             role_list[i]['speak_times'] = 0
#
#     cache.set(key, role_list)
#     return role_list