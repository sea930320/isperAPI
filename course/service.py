#!/usr/bin/python
# -*- coding=utf-8 -*-

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


def getTeacherLabels(teachers):
    teachers_label = ""
    for teacher in teachers:
        if teachers_label == "":
            teachers_label = teacher.name
            continue
        teachers_label = teachers_label + ',' + teacher.name
    if teachers_label == '':
        return ""
    return teachers_label
