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

# Super


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
                'company': item.tcompany.name if int(item.tcompany.is_default) is not 1 else '',
                'companyType': item.tcompany.companyType.name if int(item.tcompany.is_default) is not 1 else '',
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
                'company': item.tcompanymanagers_set.get().tcompany.name if len(item.tcompanymanagers_set.all()) > 0 else
                           item.t_company_set_assistants.get().name if len(item.t_company_set_assistants.all()) > 0 else '',
                'created': str(item.create_time),
                'group': item.allgroups_set.get().name if len(item.allgroups_set.all()) > 0 else
                         item.allgroups_set_assistants.get().name if len(item.allgroups_set_assistants.all()) > 0 else
                         item.tcompanymanagers_set.get().tcompany.group.name if len(item.tcompanymanagers_set.all()) > 0 else
                         item.t_company_set_assistants.get().group.name if len(item.t_company_set_assistants.all()) > 0 else '',
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
                'group': item.allgroups_set_instructors.get().name if len(item.allgroups_set_instructors.all()) > 0 else
                         item.allgroups_set_instructor_assistants.get().name if len(item.allgroups_set_instructor_assistants.all()) > 0 else '',
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


# Group


def get_group_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 2:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = Tuser.objects.get(id=request.session['_auth_user_id']).allgroups_set.get().id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        qs = Tuser.objects.filter(Q(roles=5) & Q(tcompany__group_id=group_id) & Q(is_review=1))

        if search:
            qs = qs.filter(username__icontains=search)

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
                'name': item.name,
                'company': item.tcompany.name if int(item.tcompany.is_default) is not 1 else '',
                'companyType': item.tcompany.companyType.name if int(item.tcompany.is_default) is not 1 else '',
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


def get_group_nonCompanyUsers(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 2:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = Tuser.objects.get(id=request.session['_auth_user_id']).allgroups_set.get().id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        qs = Tuser.objects.filter(Q(roles=5) & Q(is_review=0) & Q(tcompany__group_id=group_id))

        if search:
            qs = qs.filter(username__icontains=search)

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
                'username': item.username,
                'name': item.name,
                'phone': item.phone if item.phone is not None else '',
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


def get_group_changes(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 2:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        status = int(request.POST.get("status", None))
        group_id = Tuser.objects.get(id=request.session['_auth_user_id']).allgroups_set.get().id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = TGroupChange.objects.filter(user__username__icontains=search)
        else:
            qs = TGroupChange.objects.all()

        if status == 0:
            qs = qs.filter((Q(user__tcompany__group_id=group_id) & Q(sAgree=0)) | (Q(target_id=group_id) & Q(tAgree=0)))
        elif status == 1:
            qs = qs.filter(Q(target_id=group_id) & Q(tAgree=0))
        elif status == 2:
            qs = qs.filter(Q(user__tcompany__group_id=group_id) & Q(sAgree=0))

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
                'name': item.user.name,
                'sCompany': item.user.tcompany.name if item.user.tcompany.is_default == 0 else '',
                'sGroup': item.user.tcompany.group.name,
                'phone': item.user.phone,
                'reason': item.reason,
                'state': '申请加入' if item.target_id == group_id else '申请退出'
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


def set_is_review(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        is_default = Tuser.objects.get(id=request.session['_auth_user_id']).allgroups_set.get().default
        if request.session['login_type'] != 2 | is_default == 0:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        selected = eval(request.POST.get("ids", ''))
        set = request.POST.get("set", '')

        Tuser.objects.filter(id__in=selected).update(is_review=set)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_group_change(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        selected = eval(request.POST.get("ids", ''))
        set = int(request.POST.get("set", None))
        group_id = Tuser.objects.get(id=request.session['_auth_user_id']).allgroups_set.get().id

        if request.session['login_type'] != 2 | set is None:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if set == 0:
            TGroupChange.objects.filter(id__in=selected).delete()
        else:
            for itemId in selected:
                item = TGroupChange.objects.filter(id=itemId)
                item.update(tAgree=1) if item[0].target_id == group_id else item.update(sAgree=1)
                if item[0].tAgree == item[0].sAgree == 1:
                    Tuser.objects.filter(id=item[0].user_id).update(tcompany=TCompany.objects.get(Q(group_id=item[0].target_id) & Q(is_default=1)))
                    item[0].delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_normal_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Common


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


def is_default_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 2:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        uid = request.session['_auth_user_id']

        if Tuser.objects.get(id=uid).allgroups_set.get().default == 1:
            results = 'success'
        else:
            results = 'no'

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('reset_user_password Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
