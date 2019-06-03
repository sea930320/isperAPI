from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse
from utils import code, const, public_fun, tools
from django.db.models import Q
from django.forms.models import model_to_dict
import json
from account.models import TCompanyType, OfficeItems, OfficeKinds, TJobType, TCourseItems, TCourseKinds

logger = logging.getLogger(__name__)


def get_dic_data(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] not in [1, 5]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        company = [{'id': item.id, 'name': item.name, 'content': item.content} for item in TCompanyType.objects.all()]
        job = [{'id': item.id, 'name': item.name, 'content': item.content} for item in TJobType.objects.all()]
        office = [{
            'id': item.id,
            'name': item.name,
            'content': item.content,
            'subItems': [{'sid': subitem.id, 'sname': subitem.name, 'scontent': subitem.content} for subitem in item.officeitems_set.all()]
        } for item in OfficeKinds.objects.all()]
        course = [{
            'id': item.id,
            'name': item.name,
            'content': item.content,
            'subItems': [{'sid': subitem.id, 'sname': subitem.name, 'scontent': subitem.content} for subitem in item.tcourseitems_set.all()]
        } for item in TCourseKinds.objects.all()]
        if request.session['login_type'] == 1:
            results = {
                'company': company,
                'job': job,
                'office': office,
                'course': course
            }
        else:
            results = {
                'office': office
            }
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_officeItem_data(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] not in [2, 6, 3, 7]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        results = [{
            'label': item.name,
            'options': [{
                'value': opt.id,
                'text': opt.name
            } for opt in OfficeItems.objects.filter(kinds_id=item.id)]
        } for item in OfficeKinds.objects.all()]
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_dic_data Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def new_item_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)
        target = int(request.POST.get("target", None))
        name = request.POST.get("name", '')
        content = request.POST.get("content", '')

        if target == 1:
            TCompanyType(
                name=name,
                content=content
            ).save()
        elif target == 2:
            OfficeKinds(
                name=name,
                content=content
            ).save()
        elif target == 3:
            TJobType(
                name=name,
                content=content
            ).save()
        elif target == 4:
            TCourseKinds(
                name=name,
                content=content
            ).save()
        elif target == 20:
            OfficeItems(
                name=name,
                content=content,
                kinds_id=id
            ).save()
        elif target == 40:
            TCourseItems(
                name=name,
                content=content,
                kinds_id=id
            ).save()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('new_item_save Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def edit_item_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)
        target = int(request.POST.get("target", None))
        name = request.POST.get("name", '')
        content = request.POST.get("content", '')

        if target == 1:
            TCompanyType.objects.filter(id=id).update(name=name,content=content)
        elif target == 2:
            OfficeKinds.objects.filter(id=id).update(name=name, content=content)
        elif target == 3:
            TJobType.objects.filter(id=id).update(name=name, content=content)
        elif target == 4:
            TCourseKinds.objects.filter(id=id).update(name=name, content=content)
        elif target == 20:
            OfficeItems.objects.filter(id=id).update(name=name, content=content)
        elif target == 40:
            TCourseItems.objects.filter(id=id).update(name=name, content=content)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('edit_item_save Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def delete_item_save(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.POST.get("id", None)
        target = int(request.POST.get("target", None))

        if target == 1:
            TCompanyType.objects.get(id=id).delete()
        elif target == 2:
            OfficeKinds.objects.get(id=id).delete()
        elif target == 3:
            TJobType.objects.get(id=id).delete()
        elif target == 4:
            TCourseKinds.objects.get(id=id).delete()
        elif target == 20:
            OfficeItems.objects.get(id=id).delete()
        elif target == 40:
            TCourseItems.objects.get(id=id).delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('delete_item_save Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
