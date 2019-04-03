# -*- coding: utf-8 -*-
import json

from functools import wraps

from django.http import HttpResponse

from utils import code


def api_login_required(method=None):
    """
    判断用户是否需要登录装饰器
    :param method: 请求方法
    :return:
    """
    # TODO 报错，待修改
    def test_func(u):
        return u.is_authenticated

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                if method and method.upper() == request.method:
                    return func(*args, **kwargs)
                else:
                    resp = {}
                    return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type='application/json')
            else:
                resp = code.get_msg(code.USER_NOT_LOGGED_IN)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type='application/json')

        return wrapper

    return decorator
