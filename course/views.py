#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging

import re
import xlrd
import xlwt

from account.models import TClass
from django.utils.http import urlquote

from django.db.models import Q, Count
from django.http import HttpResponse
from course.models import *
from project.models import Project
from team.models import TeamMember
from utils import code, const, query
from utils.request_auth import auth_check

logger = logging.getLogger(__name__)


# 课程列表
def api_course_list(request):
    try:
        search = request.GET.get("search", None)  # 搜索关键字

        if search:
            qs = Course.objects.filter(Q(name__icontains=search))
        else:
            qs = Course.objects.all()

        data = [{'value': item.id, 'text': item.courseName} for item in qs]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': data}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_course_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
