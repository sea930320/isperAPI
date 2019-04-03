# -*- coding: utf-8 -*-
import logging
from models import Parameter, AppRelease
from django.http import HttpResponse
from utils import const, code
import json

logger = logging.getLogger(__name__)


def get_parameter(key, value=None, name=None):
    """
    功能说明:   获得参数值
    """
    val = None
    try:
        obj = Parameter.objects.filter(key=key, del_flag=const.DELETE_FLAG_NO).first()
        if obj is None:
            if value:
                Parameter.objects.create(key=key, value=value, name=name)
                val = value
        else:
            val = obj.value
    except Exception as e:
        logger.info(key)
        logger.exception('get_parameter Exception:%s' % str(e))
    return val


def set_parameter(key, value, name=None):
    """
    功能说明:   设置参数值
    """
    try:
        obj = Parameter.objects.filter(key=key, del_flag=const.DELETE_FLAG_NO).first()
        if obj is None:
            Parameter.objects.create(key=key, value=value, name=name)
        else:
            obj.value = value
            obj.save()
    except Exception as e:
        logger.info(key)
        logger.exception('set_parameter Exception:%s' % str(e))


def get_user_ip(request):
    """
    功能说明:   获取用户ip
    """
    try:
        logger.info(request.META)
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
    except KeyError:
        ip = ''
    return ip


def check_app_version(request):
    """
    功能说明：   检测app版本
    """
    device = request.GET.get('device', None)
    ver = request.GET.get('ver', 1)

    if device is None:
        resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        device = int(device)
        if device not in (1, 2):
            resp = code.get_msg(code.PARAMETER_ERROR)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        app = AppRelease.objects.filter(type=device, del_flag=const.DELETE_FLAG_NO).first()
        if app:
            resp = code.get_msg(code.SUCCESS)
            if app.version > int(ver):
                resp['d'] = {'has_update': True, 'version': app.version, 'url': app.url, 'desc': app.remark}
            else:
                resp['d'] = {'has_update': False}
        else:
            resp = code.get_msg(code.SYSTEM_ERROR)
    except Exception as e:
        logger.exception('api_project_roles_detail Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def app_url():
    """
    功能说明：   app下载地址
    """
    result = {}
    try:
        android_url = ''
        ios_url = ''
        android = AppRelease.objects.filter(type=const.DEVICE_ANDROID).first()
        if android:
            android_url = android.url

        ios = AppRelease.objects.filter(type=const.DEVICE_IOS).first()
        if ios:
            ios_url = ios.url

        result = {'android': android_url, 'ios': ios_url}
    except Exception as e:
        logger.exception('app_url Exception:%s' % str(e))
    return result
