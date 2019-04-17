#!/usr/bin/python
# -*- coding=utf-8 -*-

import json
import logging

from django.http import HttpResponse

from account.service import user_simple_info
from system.models import UploadFile
from utils import code
from utils.request_auth import auth_check

logger = logging.getLogger(__name__)


# 上传文件
def api_file_upload(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        upload_file = request.FILES.get("file", None)  # 文件

        if upload_file:
            obj = UploadFile.objects.create(filename=upload_file.name, file=upload_file, created_by=request.user.id)

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {
                'id': obj.id, 'filename': obj.filename, 'url': obj.file.url, 'md5sum': obj.md5sum,
                'create_time': obj.create_time.strftime('%Y-%m-%d'), 'created_by': user_simple_info(obj.created_by)
            }
        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
    except Exception as e:
        logger.exception('api_file_upload Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)

    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def file_info(file_id):
    obj = UploadFile.objects.filter(pk=file_id).first()
    if obj:
        result = {
            'id': obj.id, 'filename': obj.filename, 'url': obj.file.url, 'md5sum': obj.md5sum,
            'create_time': obj.create_time is not None and obj.create_time.strftime('%Y-%m-%d') or ""
        }
        return result
    else:
        return None
