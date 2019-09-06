# coding=utf-8
import os

from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse, Http404
from utils import code, const, public_fun, tools
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.forms.models import model_to_dict
import json
from django.conf import settings
from account.models import *
from group.models import *
from utils.permission import permission_check

logger = logging.getLogger(__name__)


# Super


def get_normal_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] not in [1, 2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        company_id = request.POST.get("company_id", None)
        part_id = request.POST.get("part_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))
        except_group_assistant = 0 if request.POST.get("except_group_assistant") is None else int(
            request.POST.get("except_group_assistant"))
        except_company_assistant = 0 if request.POST.get("except_company_assistant") is None else int(
            request.POST.get("except_company_assistant"))

        if search:
            qs = Tuser.objects.filter(Q(roles=5) & Q(username__icontains=search))
        else:
            qs = Tuser.objects.filter(roles=5)

        if group_id:
            qs = qs.filter(tcompany__group_id=group_id)
        if company_id:
            qs = qs.filter(tcompany__id=company_id)
        if part_id:
            qs = qs.filter(tposition__parts__id=part_id)
        if except_group_assistant != 0 and group_id:
            qs = qs.exclude(Q(roles=6) | Q(allgroups_set_assistants__id=group_id))
        if except_company_assistant != 0 and company_id:
            qs = qs.exclude(Q(roles=7) | Q(t_company_set_assistants__id=company_id))

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
                'company': item.tcompany.name if int(item.tcompany.is_default) is not 1 else '',
                'part': item.tposition.parts.name if item.tposition is not None else '',
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
        if request.session['login_type'] not in [1, 2, 3]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = request.POST.get("group_id", None)
        company_id = request.POST.get("company_id", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))
        except_group_assistant = 0 if request.POST.get("except_group_assistant") is None else int(
            request.POST.get("except_group_assistant"))
        except_company_assistant = 0 if request.POST.get("except_company_assistant") is None else int(
            request.POST.get("except_company_assistant"))

        if search:
            qs = Tuser.objects.filter(Q(roles__in=[2, 3, 6, 7]) & Q(username__icontains=search)).distinct()
        else:
            qs = Tuser.objects.filter(roles__in=[2, 3, 6, 7]).distinct()

        if group_id:
            qs = qs.filter(Q(allgroups_set__id=group_id) |
                           Q(allgroups_set_assistants__id=group_id) |
                           Q(tcompanymanagers__tcompany__group_id=group_id) |
                           Q(t_company_set_assistants__group_id=group_id))
        if company_id:
            qs = qs.filter(Q(tcompanymanagers__tcompany__id=company_id) | Q(t_company_set_assistants__id=company_id))
        if except_group_assistant != 0 and group_id:
            qs = qs.exclude(Q(roles=6) | Q(allgroups_set_assistants__id=group_id))
        if except_company_assistant != 0 and company_id:
            qs = qs.exclude(Q(roles=7) | Q(t_company_set_assistants__id=company_id))

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                users = paginator.page(page)
            except EmptyPage:
                users = paginator.page(1)
        results = []
        for item in users:
            company = None
            role = None
            if group_id:
                role = u'集群管理员' if (item.allgroups_set.filter(Q(id=group_id))) else u'集群管理员助理' if (
                    item.allgroups_set_assistants.filter(Q(id=group_id))) else u'单位管理员' if (
                    item.tcompanymanagers_set.filter(Q(tcompany__group_id=group_id))) else '单位管理员助理' if (
                    item.t_company_set_assistants.filter(Q(group_id=group_id))) else ''
                company = item.tcompanymanagers_set.get().tcompany.name if item.tcompanymanagers_set.filter(
                    Q(
                        tcompany__group__id=group_id)) else item.t_company_set_assistants.get().name if item.t_company_set_assistants.filter(
                    Q(group__id=group_id)) else ''
            if company_id:
                role = u'单位管理员' if (item.tcompanymanagers_set.filter(Q(tcompany__id=company_id))) else u'单位管理员助理' if (
                    item.t_company_set_assistants.filter(Q(id=company_id))) else ''
                company = item.tcompanymanagers_set.get().tcompany.name if item.tcompanymanagers_set.filter(
                    Q(
                        tcompany__id=company_id)) else item.t_company_set_assistants.get().name if item.t_company_set_assistants.filter(
                    Q(id=company_id)) else ''
            if company is None:
                company = item.tcompanymanagers_set.get().tcompany.name if len(
                    item.tcompanymanagers_set.all()) > 0 else item.t_company_set_assistants.get().name if len(
                    item.t_company_set_assistants.all()) > 0 else ''
            if role is None:
                role = u'集群管理员' if len(item.allgroups_set.all())>0 else u'集群管理员助理' if len(
                    item.allgroups_set_assistants.filter())>0 else u'单位管理员' if len(
                    item.tcompanymanagers_set.all())>0 else '单位管理员助理' if len(
                    item.t_company_set_assistants.all())>0 else ''
            result = {
                'id': item.id,
                'name': item.username,
                'company': company,
                'created': item.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'group': item.allgroups_set.get().name if len(item.allgroups_set.all()) > 0 else
                item.allgroups_set_assistants.get().name if len(item.allgroups_set_assistants.all()) > 0 else
                item.tcompanymanagers_set.get().tcompany.group.name if len(item.tcompanymanagers_set.all()) > 0 else
                item.t_company_set_assistants.get().group.name if len(item.t_company_set_assistants.all()) > 0 else '',
                'role': role
            }
            results.append(result)

        paging = {
            'count': paginator.count,
            'has_previous': users.has_previous(),
            'has_next': users.has_next(),
            'num_pages': paginator.num_pages,
            'cur_page': users.number,
        }

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'paging': paging}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('get_manage_users Exception:{0}'.format(str(e)))
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
            qs = qs.filter(
                Q(allgroups_set_instructors__id=group_id) | Q(allgroups_set_instructor_assistants__id=group_id))

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
                'officeItem': [i.name for i in item.instructorItems.all()] if len(
                    item.instructorItems.all()) > 0 else [],
                'created': item.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'group': item.allgroups_set_instructors.get().name if len(item.allgroups_set_instructors.all()) > 0 else
                item.allgroups_set_instructor_assistants.get().name if len(
                    item.allgroups_set_instructor_assistants.all()) > 0 else '',
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
        logger.exception('get_instructor_users Exception:{0}'.format(str(e)))
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
        logger.exception('get_student_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Group


def get_group_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id
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
                'gender': '男' if item.gender == 1 else '女',
                'company': item.tcompany.name if int(item.tcompany.is_default) is not 1 else '',
                'part': item.tposition.parts.name if item.tposition is not None else '',
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
        logger.exception('get_group_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_group_nonCompanyUsers(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        group_id = user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id
        default_company_id = TCompany.objects.get(Q(group_id=group_id)&Q(is_default=1)).id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        qs = Tuser.objects.filter(Q(roles=5) & Q(is_review=0) & Q(tcompany_id=default_company_id))

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
                'gender': '男' if item.gender == 1 else '女',
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
        logger.exception('get_group_nonCompanyUsers Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_group_changes(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        status = int(request.POST.get("status", None))
        group_id = user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id
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
                'gender': '男' if item.user.gender == 1 else '女',
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
        logger.exception('get_group_changes Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_is_review(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_user_review_user'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        role = request.session['login_type']
        role = 2 if role == 6 else 3 if role == 7 else role
        selected = eval(request.POST.get("ids", ''))
        set = request.POST.get("set", '')

        Tuser.objects.filter(id__in=selected).update(is_review=set)

        for uid in selected:
            try:
                user = TNotifications.objects.get(Q(type='registerEvent_' + str(uid)) & Q(role=role))
            except Exception as e:
                continue
            if user.mode == 0:
                user.delete()
            elif user.mode == 1:
                user.targets.remove(Tuser.objects.get(id=request.session['_auth_user_id']))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('set_is_review Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_group_change(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_change_group_company_user'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        selected = eval(request.POST.get("ids", ''))
        set = int(request.POST.get("set", None))
        login_type = request.session['login_type']
        user = request.user

        if login_type not in [2, 6] or set is None:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        group_id = user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id if login_type == 6 else None
        if set == 0:
            TGroupChange.objects.filter(id__in=selected).delete()
        else:
            for itemId in selected:
                item = TGroupChange.objects.filter(id=itemId)
                item.update(tAgree=1) if item[0].target_id == group_id else item.update(sAgree=1)
                if item[0].tAgree == item[0].sAgree == 1:
                    Tuser.objects.filter(id=item[0].user_id).update(
                        tcompany=TCompany.objects.get(Q(group_id=item[0].target_id) & Q(is_default=1)),
                        tposition_id=None)
                    item[0].delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('set_group_change Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Company


def get_company_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        company = user.tcompanymanagers_set.get().tcompany if login_type == 3 else user.t_company_set_assistants.get()
        company_id = company.id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        qs = Tuser.objects.filter(Q(roles__in=[5, 9]) & Q(tcompany=company_id) & Q(is_review=1)).order_by('-id')

        positions = [{
            'label': item.name,
            'options': [{
                'value': opt.id,
                'text': opt.name
            } for opt in TPositions.objects.filter(parts_id=item.id)]
        } for item in TParts.objects.filter(company_id=company_id)]

        if search:
            qs = qs.filter(name__icontains=search)

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}, 'positions': positions}
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
                'username': item.username,
                'email': item.email,
                'gender': '男' if item.gender == 1 else '女',
                'part': item.tposition.parts.name if item.tposition is not None else '',
                'position': item.tposition.name if item.tposition is not None else '',
                'phone': item.phone,
            } for item in flows]

            paging = {
                'count': paginator.count,
                'has_previous': flows.has_previous(),
                'has_next': flows.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': flows.number,
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging, 'positions': positions}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_company_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_company_excelUsers(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        excelData = request.POST.get("excelData", None)
        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        for item in json.loads(excelData):
            if len(TPositions.objects.filter(Q(name=item[u'position'].encode('utf8')) & Q(parts__in=TParts.objects.filter(Q(company_id=company_id) & Q(name=item[u'part'].encode('utf8')))))) > 0:
                position = TPositions.objects.filter(Q(name=item[u'position'].encode('utf8')) & Q(parts__in=TParts.objects.filter(Q(company_id=company_id) & Q(name=item[u'part'].encode('utf8'))))).first()
            else:
                position = None
            newUser = Tuser(
                username=item[u'username'].encode('utf8'),
                name=item[u'name'].encode('utf8'),
                password=make_password('123456'),
                phone=item[u'phone'],
                email=item[u'email'].encode('utf8'),
                is_superuser=0,
                gender=1 if item[u'gender'].encode('utf8') == '男' else 0,
                comment='',
                identity=1,
                type=1,
                is_active=1,
                is_admin=0,
                director=0,
                manage=0,
                update_time='',
                del_flag=0,
                is_register=0,
                tcompany_id=company_id,
                is_review=1,
                tposition=position
            )
            newUser.save()
            if TCompany.objects.get(pk=company_id).companyType.name == '学校':
                newUser.roles.add(TRole.objects.get(id=9))
            else:
                newUser.roles.add(TRole.objects.get(id=5))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_company_excelUsers Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_company_newUser(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        name = request.POST.get("name", None)
        username = request.POST.get("username", None)
        email = request.POST.get("email", None)
        gender = request.POST.get("gender", None)
        password = request.POST.get("password", None)
        phone = request.POST.get("phone", None)
        position = request.POST.get("position", None)
        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        is_exist = Tuser.objects.filter(username=username).exists()
        if is_exist:
            resp = code.get_msg(code.USER_EXIST_WHILE_CREATING)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        newUser = Tuser(
            username=username,
            name=name,
            password=make_password(password),
            phone=phone,
            email=email,
            is_superuser=0,
            gender=int(gender),
            comment='',
            identity=1,
            type=1,
            is_active=1,
            is_admin=0,
            director=0,
            manage=0,
            update_time='',
            del_flag=0,
            is_register=0,
            tcompany_id=company_id,
            is_review=1,
            tposition_id=position
        )
        newUser.save()
        newUser.roles.add(TRole.objects.get(id=5))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_company_newUser Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def delete_company_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        selected = eval(request.POST.get("ids", ''))
        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        for item in selected:
            user = Tuser.objects.filter(Q(id=item) & Q(roles=5) & Q(tcompany_id=company_id))
            if len(user) > 0:
                if len(user.get().roles.all()) == 1:
                    user.delete()
                else:
                    TRole.objects.get(id=5).tuser_set.remove(item)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('delete_company_users Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_group_nonReviewUsers(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        company = user.tcompanymanagers_set.get().tcompany if login_type == 3 else user.t_company_set_assistants.get()
        company_id = company.id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        qs = Tuser.objects.filter(Q(roles=5) & Q(is_review=0) & Q(tcompany_id=company_id))

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
                'gender': '男' if item.gender == 1 else '女',
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
        logger.exception('get_group_nonReviewUsers Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_company_changes(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        user = request.user
        if login_type not in [3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        status = int(request.POST.get("status", None))
        company = user.tcompanymanagers_set.get().tcompany if login_type == 3 else user.t_company_set_assistants.get()
        company_id = company.id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = TCompanyChange.objects.filter(user__username__icontains=search)
        else:
            qs = TCompanyChange.objects.all()

        if status == 0:
            qs = qs.filter((Q(user__tcompany=company_id) & Q(sAgree=0)) | (Q(target_id=company_id) & Q(tAgree=0)))
        elif status == 1:
            qs = qs.filter(Q(target_id=company_id) & Q(tAgree=0))
        elif status == 2:
            qs = qs.filter(Q(user__tcompany=company_id) & Q(sAgree=0))

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
                'gender': '男' if item.user.gender == 1 else '女',
                'sCompany': item.user.tcompany.name if item.user.tcompany.is_default == 0 else '',
                'sPosition': item.user.tposition.name if item.user.tposition is not None else '',
                'phone': item.user.phone,
                'reason': item.reason,
                'state': '申请加入' if item.target_id == company_id else '申请退出'
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
        logger.exception('get_company_changes Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_company_change(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        selected = eval(request.POST.get("ids", ''))
        set = int(request.POST.get("set", None))
        login_type = request.session['login_type']
        user = request.user
        company = user.tcompanymanagers_set.get().tcompany if login_type == 3 else user.t_company_set_assistants.get()
        company_id = company.id

        if not permission_check(request, 'code_change_group_company_user') or set is None:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if set == 0:
            TCompanyChange.objects.filter(id__in=selected).delete()
        else:
            for itemId in selected:
                item = TCompanyChange.objects.filter(id=itemId)
                item.update(tAgree=1) if item[0].target_id == company_id else item.update(sAgree=1)
                if item[0].tAgree == item[0].sAgree == 1:
                    Tuser.objects.filter(id=item[0].user_id).update(tcompany_id=item[0].target_id, tposition_id=None)
                    item[0].delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('set_company_change Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Common


def reset_user_password(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_reset_password_user'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
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


def download_sample_excel(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    file_path = os.path.join(settings.MEDIA_ROOT, u'用户列表.xls')
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'attachment; filename="用户列表.xls"'
            return response
    raise Http404
