#!/usr/bin/python
# -*- coding=utf-8 -*-

from advertising.models import *
import json
import logging
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.db import transaction
from account.service import user_simple_info
from workflow.models import *
from utils.request_auth import auth_check
from utils import code
from django.core.cache import cache
import pypandoc
from datetime import datetime
import os

logger = logging.getLogger(__name__)


# 公告列表
def api_advertising_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        if request.session['login_type'] == 1:
            search = request.GET.get("search", None)  # 搜索关键字
            page = int(request.GET.get("page", 1))  # 页码
            size = int(request.GET.get("size", const.ROW_SIZE))  # 页面条数

            qs = Advertising.objects.filter()

            if search:
                qs = qs.filter(name=search)

            user = request.user

            paginator = Paginator(qs, size)

            try:
                advertisings = paginator.page(page)
            except EmptyPage:
                advertisings = paginator.page(1)

            results = []

            for advertising in advertisings:
                results.append({
                    'id': advertising.id,
                    'name': advertising.name, 'path': advertising.path, 'file_type': advertising.file_type,
                    'created_by': user_simple_info(advertising.created_by.id),
                    # 'public_time': advertising.public_time,
                    'create_time': advertising.create_time is not None and advertising.create_time.strftime('%Y-%m-%d') or ''
                    # 'update_time': advertising.update_time is not None and advertising.update_time.strftime('%Y-%m-%d') or '',
                })
            # 信息
            paging = {
                'count': paginator.count,
                'has_previous': advertisings.has_previous(),
                'has_next': advertisings.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': advertisings.number,
                'page_size': size
            }
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_project_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_advertising_delete(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] == 1:
            advertising_id = request.POST.get("advertising_id", None)  # 项目ID
            if advertising_id is None:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            obj = Advertising.objects.filter(pk=advertising_id).first()
            if obj:
                cache.clear()
                with transaction.atomic():
                    obj = Advertising.objects.filter(id=advertising_id).delete()
                    # obj.save()
                    resp = code.get_msg(code.SUCCESS)
            else:
                resp = code.get_msg(code.PROJECT_NOT_EXIST)
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
    except Exception as e:
        logger.exception('api_project_delete Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def api_advertising_create(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        if request.session['login_type'] == 1:
            ad_name = request.POST.get("ad_name", None)  # 名称
            public_time = request.POST.get("public_time", None)
            if (public_time):
                public_time = datetime.strptime(public_time, '%Y-%m-%d')
            ad_content = request.POST.get("ad_content", None)
            # if all([ad_name]):
            name = ad_name.strip()
            if len(name) == 0 or len(name) > 32:
                resp = code.get_msg(code.PARAMETER_ERROR)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
            if (len(Advertising.objects.filter(name=ad_name)) > 0):
                resp = code.get_msg(code.ADVERTISING_NAME_ALREADY_EXISTS)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            with transaction.atomic():
                # obj = Advertising.objects.create(name=name, path=path, file_type=file_type, created_by=Tuser.objects.get(id=request.user.pk))
                if (public_time):
                    obj = Advertising.objects.create(name=ad_name, created_by=Tuser.objects.get(id=request.user.pk),
                                                 public_time=public_time)
                else:
                    obj = Advertising.objects.create(name=ad_name, created_by=Tuser.objects.get(id=request.user.pk))
                saved_data_id = obj.id
                tmp_filename = os.path.join('/advertising_documents', str(saved_data_id) + '.html')
                # docx_file_name = os.path.join('/advertising_documents',
                #                               str(saved_data_id) + '_' + ad_name + '.docx')
                docx_file_name = os.path.join('/advertising_documents',
                                              str(saved_data_id) + '.docx')


                f = open(tmp_filename, "a+")
                f.write(ad_content)
                f.close()
                pypandoc.convert_file(tmp_filename, 'docx', outputfile=docx_file_name)

                # must be updated
                docx_file_name_path = docx_file_name
                with transaction.atomic():
                    Advertising.objects.filter(id=saved_data_id).update(path=docx_file_name_path)
                    # obj = Advertising.objects.filter(id=saved_data_id)
                    resp = code.get_msg(code.SUCCESS)
                    # resp['d'] = {
                    #     'name': obj.name, 'path': obj.path, 'file_type': obj.file_type,
                    #     'created_by': obj.created_by, 'public_time': obj.public_time
                    # }
            # else:
            #     resp = code.get_msg(code.PARAMETER_ERROR)
            #     print '1'
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
    except Exception as e:
        logger.exception('api_project_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")



