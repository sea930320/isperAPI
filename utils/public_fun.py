#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import random
from project.models import *


# 构造文件名称
def makename(name):
    # 文件扩展名
    ext = os.path.splitext(name)[1]

    # 定义文件名，年月日时分秒随机数
    fn = time.strftime('%Y%m%d%H%M%S')
    fn += '_%d' % random.randint(1, 10000)
    # 重写合成文件名
    name = fn + ext
    return name


# 随机生成验证码
def randomCode(length):
    num = '0123456789'
    return ''.join(random.sample(num, length))


# 取对应值
def get_map(data, id):
    for d in data:
        if d[0] == id:
            return d[1]
    return None

# get group and company ID
def getGroupAndCompanyIDsByUserID(loginType, userID):
    # Group Manager
    if (loginType == 2):
        print loginType
    # Company Manager
    if (loginType == 3):
        Project.objects.filter(id__in=ids).update(is_share=0)
        print loginType

    print userID
    return userID

# get group memvers by user Id
def getGroupMembersByUserID(userID):
    return userID