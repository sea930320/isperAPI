# -*- coding: utf-8 -*-
from account.models import Tuser


def user_info(user_id):
    """
    获取用户所有信息
    :param user_id: 用户ID
    :return:
    """
    user = Tuser.objects.filter(pk=user_id).first()
    if user:
        result = {'username': user.username, 'gender': user.gender, 'nickname': user.nickname, 'name': user.name,
                  'email': user.email, 'phone': user.phone, 'qq': user.qq, 'identity': user.identity,
                  'type': user.type, 'ip': user.ip, 'id': user.id, 'avatar': user.avatar.url}
        return result
    else:
        return {}


def user_simple_info(user_id):
    """
    获取用户基本信息
    :param user_id: 用户ID
    :return:
    """
    user = Tuser.objects.filter(pk=user_id).first()
    if user:
        result = {'username': user.username, 'id': user.id, 'name': user.name, 'identity': user.identity,
                  'nickname': user.nickname, 'gender': user.gender}
        return result
    else:
        return {}

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
