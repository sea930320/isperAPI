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

logger = logging.getLogger(__name__)


def get_part_positions(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        results = [{
            'id': item.id,
            'name': item.name,
            'positions': [{'sid': subitem.id, 'sname': subitem.name} for subitem in item.tpositions_set.all()]
        } for item in TParts.objects.filter(company=company_id)]
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def new_part_position(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        id = request.POST.get("id", None)
        target = int(request.POST.get("target", None))
        name = request.POST.get("name", '')

        if target == 1:
            TParts(
                name=name,
                company_id=company_id
            ).save()
        elif target == 2:
            TPositions(
                name=name,
                parts_id=id
            ).save()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def delete_part_position(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)
        target = int(request.POST.get("target", None))

        if target == 1:
            TParts.objects.filter(id=id).delete()
        elif target == 2:
            TPositions.objects.filter(id=id).delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_part_users(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)

        if id == '':
            results = []
        else:
            results = [{
                'id': item.id,
                'name': item.name,
                'part': item.tposition.parts.name,
                'position': item.tposition.name,
                'newPP': ''
            }for item in Tuser.objects.filter(tposition__parts_id=id)]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_non_ppUsers(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id

        results = [{
            'id': item.id,
            'name': item.name,
            'part': '无部门',
            'position': '无职务',
            'newPP': ''
        }for item in Tuser.objects.filter(Q(tcompany_id=company_id) & Q(tposition_id=None))]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_new_pp(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = eval(request.POST.get("id", ''))
        newPP = request.POST.get("newPP", None)

        Tuser.objects.filter(id__in=id).update(tposition_id=newPP)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_inner_permissions(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        search = request.POST.get("search", None)
        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))

        if search:
            qs = TInnerPermission.objects.filter(name=search)
        else:
            qs = TInnerPermission.objects.all()

        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': {'data':[], 'items': []}, 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = {
                'data': [{
                    'id': item.id,
                    'name': item.name,
                    'comment': item.comment,
                    'ownPositions': [{
                        'id': pos.id,
                        'text': pos.name
                    }for pos in item.ownPositions.filter(parts__company_id=company_id)],
                } for item in flows],
                'items': [{'id': position.id, 'text': position.name} for position in TPositions.objects.filter(parts__company_id=6)]
            }

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
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_inner_permissions(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 3:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)
        company_id = Tuser.objects.get(id=request.session['_auth_user_id']).tcompanymanagers_set.get().tcompany.id
        items = eval(request.POST.get("items", '[]'))

        TInnerPermission.objects.get(id=id).ownPositions.remove(*TPositions.objects.filter(parts__company_id=company_id))
        TInnerPermission.objects.get(id=id).ownPositions.add(*TPositions.objects.filter(id__in=items))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
