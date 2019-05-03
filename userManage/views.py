# coding=utf-8
from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse
from utils import code, const, public_fun, tools
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.forms.models import model_to_dict
import json
from account.models import *
from group.models import *

logger = logging.getLogger(__name__)


def get_normal_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = Tuser.objects.filter(Q(roles=5) & Q(username__icontains=search))
        else:
            qs = Tuser.objects.filter(roles=5)

        if group_id:
            qs = qs.filter(tcompany__group_id=group_id)

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = [{
                'id': item.id,
                'name': item.username,
                'company': item.tcompany.name if item.tcompany is not None else '',
                'companyType': item.tcompany.companyType.name if item.tcompany is not None else '',
                'group': item.tcompany.group.name if item.tcompany is not None else '',
            } for item in flows]

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
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_manage_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = Tuser.objects.filter(Q(roles__in=[2, 3, 6, 7]) & Q(username__icontains=search)).distinct()
        else:
            qs = Tuser.objects.filter(roles__in=[2, 3, 6, 7]).distinct()

        if group_id:
            qs = qs.filter(Q(allgroups_set__id=group_id) |
                           Q(allgroups_set_assistants__id=group_id) |
                           Q(tcompanymanagers__tcompany__group_id=group_id) |
                           Q(t_company_set_assistants__group_id=group_id))

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = [{
                'id': item.id,
                'name': item.username,
                'company': item.tcompanymanagers_set.all()[0].tcompany.name if len(item.tcompanymanagers_set.all()) > 0 else '',
                'created': str(item.create_time),
                'group': item.allgroups_set.all()[0].name if len(item.allgroups_set.all()) > 0 else '',
            } for item in flows]

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
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_instructor_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = Tuser.objects.filter(Q(roles__in=[4, 8]) & Q(username__icontains=search)).distinct()
        else:
            qs = Tuser.objects.filter(roles__in=[4, 8]).distinct()

        if group_id:
            qs = qs.filter(Q(allgroups_set_instructors__id=group_id) | Q(allgroups_set_instructor_assistants__id=group_id))

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = [{
                'id': item.id,
                'name': item.username,
                'officeItem': [i.name for i in item.instructorItems.all()] if len(item.instructorItems.all()) > 0 else [],
                'created': str(item.create_time),
                'group': item.allgroups_set.all()[0].name if len(item.allgroups_set.all()) > 0 else '',
            } for item in flows]

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
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_student_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = Tuser.objects.filter(Q(roles=9) & Q(username__icontains=search))
        else:
            qs = Tuser.objects.filter(roles=9)

        if group_id:
            qs = qs.filter(tcompany__group_id=group_id)

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = [{
                'id': item.id,
                'name': item.username,
                'gender': '男' if item.gender == 1 else '女',
                'class_name': item.class_name,
                'student_id': item.student_id,
                'company': item.tcompany.name if item.tcompany is not None else '',
                'group': item.tcompany.group.name if item.tcompany is not None else '',
            } for item in flows]

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
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def reset_user_password(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        uid = request.POST.get("id", None)
        password = request.POST.get("password", None)

        Tuser.objects.filter(id=uid).update(password=make_password(password))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('reset_user_password Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
