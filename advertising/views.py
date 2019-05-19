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
from system.views import api_file_upload
from system.models import UploadFile
import os
import shutil
from system.views import file_info
import codecs

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

            paginator = Paginator(qs, size)

            try:
                advertisings = paginator.page(page)
            except EmptyPage:
                advertisings = paginator.page(1)

            results = []

            for advertising in advertisings:
                path_html_file = UploadFile.objects.get(id=advertising.path_html)
                path_docx_file = UploadFile.objects.get(id=advertising.path_docx)

                results.append({
                    'id': advertising.id,
                    'name': advertising.name, 'path_html': file_info(advertising.path_html)['url'], 'path_docx': file_info(advertising.path_docx)['url'], 'file_type': advertising.file_type,
                    'created_by': user_simple_info(advertising.created_by.id),
                    'create_time': advertising.create_time is not None and advertising.create_time.strftime('%Y-%m-%d') or ''
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
        logger.exception('api_advertising_list Exception:{0}'.format(str(e)))
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
                    resp = code.get_msg(code.SUCCESS)
            else:
                resp = code.get_msg(code.SYSTEM_ERROR)
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
    except Exception as e:
        logger.exception('api_advertising_delete Exception:{0}'.format(str(e)))
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
                if (public_time):
                    obj = Advertising.objects.create(name=ad_name, created_by=Tuser.objects.get(id=request.user.pk),
                                                 public_time=public_time)
                else:
                    obj = Advertising.objects.create(name=ad_name, created_by=Tuser.objects.get(id=request.user.pk))
                saved_data_id = obj.id
                tmp_filename = str(saved_data_id)+'.html'
                docx_file_name = str(saved_data_id)+'.docx'
                
                # saved_data_name = obj.name
                # tmp_filename = str(saved_data_name).encode('utf-8')+'.html'
                # docx_file_name = str(saved_data_name).encode('utf-8')+'.docx'
                # tmp_filename = str(saved_data_name)+'.html'
                # docx_file_name = str(saved_data_name)+'.docx'

                f=codecs.open(tmp_filename, "a+", "utf-8")
                f.write(ad_content)
                f.close()

                # f = open(tmp_filename, "a+")
                # f.write(ad_content)
                # f.close()
                
                pypandoc.convert_file(tmp_filename, 'docx', outputfile=docx_file_name)
                print docx_file_name
                shutil.move(docx_file_name, 'media/files/advertising/' + docx_file_name)
                shutil.move(tmp_filename, 'media/files/advertising/' + tmp_filename)
                obj = UploadFile.objects.create(filename=docx_file_name, file='files/advertising/' + docx_file_name, created_by=request.user.id)
                pathDocx = obj.id
                print pathDocx
                obj1 = UploadFile.objects.create(filename=tmp_filename, file='files/advertising/' + tmp_filename, created_by=request.user.id)
                pathHtml = obj1.id
                print pathHtml

                with transaction.atomic():
                    Advertising.objects.filter(id=saved_data_id).update(path_docx=pathDocx,path_html=pathHtml)
                    resp = code.get_msg(code.SUCCESS)
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
    except Exception as e:
        logger.exception('api_advertising_create Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")