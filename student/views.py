#!/usr/bin/python
# -*- coding=utf-8 -*-

# from django.shortcuts import
import json
import logging
import random
from platform import node
import re
import xlrd
import xlwt
from django.utils.http import urlquote

from django.utils.timezone import now

from account.models import Tuser, TNotifications, TInnerPermission
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, F, Count
from django.http import HttpResponse
from business.models import *
from business.service import *
from project.models import Project, ProjectRole, ProjectRoleAllocation, ProjectDoc, ProjectDocRole
from team.models import Team, TeamMember
from utils import const, code, tools, easemob
from utils.request_auth import auth_check
from workflow.models import FlowNode, FlowAction, FlowRoleActionNew, FlowRolePosition, \
    FlowPosition, RoleImage, Flow, ProcessRoleActionNew, FlowDocs, FlowRole, FlowRoleAllocation, \
    FlowRoleAllocationAction, ProcessRoleAllocationAction, FlowNodeSelectDecide, SelectDecideItem
from workflow.service import get_start_node, bpmn_color
from datetime import datetime
from django.utils import timezone
import random
import string
from utils.public_fun import getProjectIDByGroupManager, \
    getProjectIDByCompanyManager, \
    getProjectIDByCompanyManagerAssistant, \
    getProjectIDByGroupManagerAssistant
from django.forms.models import model_to_dict
from socketio.socketIO_client import SocketIO, LoggingNamespace
import codecs
import pypandoc
from system.models import UploadFile
import html2text
