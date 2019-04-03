#!/usr/bin/python
# -*- coding=utf-8 -*-
from requests.auth import AuthBase
from datetime import datetime
from system import service as sys_service
from time import time
import string
import requests
import sys
import json
import logging

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)

DEBUG = True

# 环信相关的参数
JSON_HEADER = {'content-type': 'application/json'}
EASEMOB_HOST = "https://a1.easemob.com"
ORG_NAME = '1167170120178531'
APP_NAME = 'lets2017'
APP_KEY = '1167170120178531#lets2017'
CLIENT_ID = 'YXA66DM4QPMhEeaeVcOsWl3jbA'
CLIENT_SECRET = 'YXA6iSR4ja5BrgED25wZAOoGHDmhANU'

EASEMOB_PASSWORD = 'dGVkX18a7lZ81GmpE'
EASEMOB_TOKEN_KEY = 'EASEMOB_TOKEN'
EASEMOB_TOKEN_NAME = u'环信TOKEN'
EASEMOB_TOKEN_EXIPRES_KEY = 'EASEMOB_EXIPRES'
EASEMOB_TOKEN_EXIPRES_NAME = u'环信TOKEN有效时间'

TARGET_TYPE_USER = 'users'
TARGET_TYPE_GROUP = 'chatgroups'
MSG_TXT_TYPE = 'txt'

# 消息标示
MESSAGE_LOGOUT_FLAG = 99

PAGE_SIZE = '100'
MESSAGE_PRE_DAYS = 30


def post(url, payload, auth=None):
    r = requests.post(url, data=json.dumps(payload), headers=JSON_HEADER, auth=auth)
    return http_result(r)


def put(url, payload, auth=None):
    r = requests.put(url, data=json.dumps(payload), headers=JSON_HEADER, auth=auth)
    return http_result(r)


def get(url, auth=None):
    r = requests.get(url, headers=JSON_HEADER, auth=auth)
    return http_result(r)


def delete(url, auth=None):
    r = requests.delete(url, headers=JSON_HEADER, auth=auth)
    return http_result(r)


def http_result(r):
    if DEBUG:
        error_log = {
            "method": r.request.method,
            "url": r.request.url,
            "request_header": dict(r.request.headers),
            "response_header": dict(r.headers),
            "response": r.text
        }
        if r.request.body:
            error_log["payload"] = r.request.body
        logger.info(json.dumps(error_log))

    if r.status_code == requests.codes.ok:
        return True, r.json()
    else:
        return False, r.text


class Token:
    """表示一个登陆获取到的token对象"""

    def __init__(self, token, exipres_in):
        self.token = token
        self.exipres_in = exipres_in

    def is_not_valid(self):
        """这个token是否还合法, 或者说, 是否已经失效了, 这里我们只需要
        检查当前的时间, 是否已经比或者这个token的时间过去了exipreis_in秒

        即  current_time_in_seconds < (expires_in + token_acquired_time)
        """
        return time() > self.exipres_in


class EasemobAuth(AuthBase):
    """环信登陆认证的基类"""

    def __init__(self):
        self.token = ""

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.get_token()
        return r

    def get_token(self):
        """先检查是否已经获取过token, 并且这个token有没有过期"""
        access_token = sys_service.get_parameter(EASEMOB_TOKEN_KEY)
        expires_in = sys_service.get_parameter(EASEMOB_TOKEN_EXIPRES_KEY)
        if access_token and expires_in:
            self.token = Token(access_token, int(expires_in))

        if (self.token is None) or (self.token.is_not_valid()):
            # refresh the token
            self.token = self.acquire_token()

        return self.token.token

    def acquire_token(self):
        """真正的获取token的方法, 返回值是一个我们定义的Token对象
            这个留给子类去实现
        """
        pass


class AppClientAuth(EasemobAuth):
    """使用app的client_id和client_secret来获取app管理员token"""

    def __init__(self):
        super(AppClientAuth, self).__init__()
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.url = EASEMOB_HOST + ("/%s/%s/token" % (ORG_NAME, APP_NAME))
        self.token = None

    def acquire_token(self):
        """
        使用client_id / client_secret来获取token, 具体的REST API为

        POST /{org}/{app}/token {'grant_type':'client_credentials', 'client_id':'xxxx', 'client_secret':'xxxxx'}
        """
        payload = {'grant_type': 'client_credentials', 'client_id': self.client_id,
                   'client_secret': self.client_secret}
        success, result = post(self.url, payload)
        if success:
            sys_service.set_parameter(EASEMOB_TOKEN_KEY, result['access_token'], EASEMOB_TOKEN_NAME)
            expires_in = result['expires_in'] + int(time()) - 1000
            # expires_in = result['expires_in']
            sys_service.set_parameter(EASEMOB_TOKEN_EXIPRES_KEY, expires_in, EASEMOB_TOKEN_EXIPRES_NAME)
            return Token(result['access_token'], result['expires_in'])
        else:
            # throws exception
            pass


def register_new_user(username, password):
    """注册新的app用户
    POST /{org}/{app}/users {"username":"xxxxx", "password":"yyyyy"}
    """
    auth = AppClientAuth()
    payload = {"username": username, "password": password}
    url = EASEMOB_HOST + ("/%s/%s/users" % (ORG_NAME, APP_NAME))
    return post(url, payload, auth)


def delete_user(username):
    """删除app用户
    DELETE /{org}/{app}/users/{username}
    """
    auth = AppClientAuth()
    url = EASEMOB_HOST + ("/%s/%s/users/%s" % (ORG_NAME, APP_NAME, username))
    return delete(url, auth)


def update_nickname(username, nickname):
    """修改用户昵称
    Path: /{org_name}/{app_name}/users/{username}
    """
    auth = AppClientAuth()
    payload = {"nickname": nickname}
    url = EASEMOB_HOST + ("/%s/%s/users/%s" % (ORG_NAME, APP_NAME, username))
    return put(url, payload, auth)


def contacts_add(owner_username, friend_username):
    """用户添加好友
    POST  /{org_name}/{app_name}/users/{owner_username}/contacts/users/{friend_username}
    """
    auth = AppClientAuth()
    payload = {}
    url = EASEMOB_HOST + ("/%s/%s/users/%s/contacts/users/%s" % (ORG_NAME, APP_NAME, owner_username, friend_username))
    return post(url, payload, auth)


def contacts_delete(owner_username, friend_username):
    """解除 IM 用户的好友关系
    POST  /{org_name}/{app_name}/users/{owner_username}/contacts/users/{friend_username}
    """
    auth = AppClientAuth()
    url = EASEMOB_HOST + ("/%s/%s/users/%s/contacts/users/%s" % (ORG_NAME, APP_NAME, owner_username, friend_username))
    return delete(url, auth)


def create_groups(group_id, owner, members=None):
    """创建一个群组
    POST /{org}/{app}/chatgroups
    {
        "groupname":"testrestgrp12", //群组名称，此属性为必须的
        "desc":"server create group", //群组描述，此属性为必须的
        "public":true, //是否是公开群，此属性为必须的
        "maxusers":300, //群组成员最大数（包括群主），值为数值类型，默认值200，最大值2000，此属性为可选的
        "approval":true, //加入公开群是否需要批准，默认值是false（加入公开群不需要群主批准），此属性为必选的，私有群必须为true
        "owner":"jma1", //群组的管理员，此属性为必须的
        "members":["jma2","jma3"] //群组成员，此属性为可选的，但是如果加了此项，数组元素至少一个（注：群主jma1不需要写入到members里面）
    }
    """
    auth = AppClientAuth()
    payload = {'groupname': group_id, 'desc': group_id, 'public': True, 'maxusers': 2000, 'owner': owner}
    if members:
        payload['members'] = members
    url = EASEMOB_HOST + ("/%s/%s/chatgroups" % (ORG_NAME, APP_NAME))
    return post(url, payload, auth)


def delete_groups(group_id):
    """删除群组
    Path: /{org_name}/{app_name}/chatgroups/{group_id}
    """
    auth = AppClientAuth()
    url = EASEMOB_HOST + ("/%s/%s/chatgroups/%s" % (ORG_NAME, APP_NAME, group_id))
    return delete(url, auth)


def add_groups_member(group_id, members):
    """添加群组成员[批量]
    Path: /{org_name}/{app_name}/chatgroups/{chatgroupid}/users
    {“usernames”:[“username1”,”username2”]}
    """
    auth = AppClientAuth()
    m = []
    for item in members:
        m.append(str(item))
    payload = {'usernames': m}
    url = EASEMOB_HOST + ("/%s/%s/chatgroups/%s/users" % (ORG_NAME, APP_NAME, group_id))
    return post(url, payload, auth)


def delete_groups_member(group_id, username):
    """移除群组成员
    Path: /{org_name}/{app_name}/chatgroups/{group_id}/users/{username}
    """
    auth = AppClientAuth()
    url = EASEMOB_HOST + ("/%s/%s/chatgroups/%s/users/%s" % (ORG_NAME, APP_NAME, group_id, username))
    return delete(url, auth)


def send_message(target_type, target, msg, from_obj=None, ext=None):
    """发送消息
    Path: /{org_name}/{app_name}/messages
    {
        "target_type":"users",     // users 给用户发消息。chatgroups 给群发消息，chatrooms 给聊天室发消息
        "target":["testb","testc"], // 注意这里需要用数组，数组长度建议不大于20，即使只有
                                    // 一个用户u1或者群组，也要用数组形式 ['u1']，给用户发
                                    // 送时数组元素是用户名，给群组发送时数组元素是groupid
        "msg":{  //消息内容
            "type":"txt",  // 消息类型，不局限与文本消息。任何消息类型都可以加扩展消息
            "msg":"消息"    // 随意传入都可以
        },
        "from":"testa",  //表示消息发送者。无此字段Server会默认设置为"from":"admin"，有from字段但值为空串("")时请求失败
        "ext":{   //扩展属性，由APP自己定义。可以没有这个字段，但是如果有，值不能是"ext:null"这种形式，否则出错
            "attr1":"v1"   // 消息的扩展内容，可以增加字段，扩展消息主要解析部分，必须是基本类型数据。
        }
    }
    """
    auth = AppClientAuth()
    payload = {'target_type': target_type, 'target': target, 'msg': msg}
    if from_obj:
        payload['from'] = from_obj
    if ext:
        payload['ext'] = ext
    url = EASEMOB_HOST + ("/%s/%s/messages" % (ORG_NAME, APP_NAME))
    return post(url, payload, auth)


def get_history_message():
    """
    查询环信的聊天历史消息
    :return: SUCCESS or FAIL
    """
    logger.info("-------huanxin---get_history_message--------")
    auth = AppClientAuth()

    # time_obj = get_obj_by_key('huanxin_time')
    # cur_obj = get_obj_by_key('huanxin_curse')
    # if time_obj.value_str and time_obj.value_str != '' and cur_obj.value_str and cur_obj.value_str != '':
    #     time_strap = time_obj.value_str
    #     url = HUAN_XIN_GET_HISTORY_MESSAGE + '?ql=select+*+where+timestamp>'
    #     url += time_strap
    #     url += "&limit="+HUAN_XIN_PAGE_SIZE
    #     url += "&cursor=" + cur_obj.value_str
    # elif time_obj.value_str and time_obj.value_str != '':
    #     time_strap = time_obj.value_str
    #     url = HUAN_XIN_GET_HISTORY_MESSAGE + '?ql=select+*+where+timestamp>'+time_strap
    #     url += "&limit="+HUAN_XIN_PAGE_SIZE
    # else:
    #     time_strap = datetime.datetime.now() - datetime.timedelta(days=HUAN_XIN_MESSAGE_PRE_DAYS)
    #     time_str = str(int(1000 * time.mktime(time_strap.timetuple())))
    #     url = HUAN_XIN_GET_HISTORY_MESSAGE + '?ql=select+*+where+timestamp>'
    #     url += time_str
    #     url += "&limit="+HUAN_XIN_PAGE_SIZE
    #     time_obj.value_str = time_str
    #     save_obj(time_obj)



#         json_data = {
#             "target_type": 'chatgroups',
#             'target': [cms_base.group.huanxin_id],
#             'msg': {
#                 'type': 'cmd',
#                 'action': 'action1'
#             },
#             'from': 'admin',
#             'ext': {
#                 'title': title,
#                 'cms_id': cms_base.id,
#                 'group_id': cms_base.group.id,
#                 'huanxin_id': cms_base.group.huanxin_id,
#                 'avatar': avatar,
#                 'at_ids': at_ids,
#                 'sender': member.nickname,
#                 'function': cms_base.function.name,
#                 'time': cms_base.create_time.strftime(utils.FORMAT_DATETIME),
#             }
#         }
#