#!/usr/bin/python
# -*- coding: utf-8 -*-


from utils import code


def auth_check(request, method="POST", login_check=True):
    resp = {}

    if login_check:
        if not request.user.is_authenticated():
            resp = code.get_msg(code.USER_NOT_LOGGED_IN)
            return resp
    else:
        return resp

    if request.method != method.upper():
        resp = code.get_msg(code.METHOD_NOT_ALLOW)

    return resp
