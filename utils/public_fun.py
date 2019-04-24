#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import random
from account.models import *
from group.models import *
from group.models import AllGroups
import json
import code


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
def getGroupByGroupManagerID(loginType, userID):
    res = {}
    # Group Manager
    if (loginType == 2):
        # Group Manager
        try:
            res['login_type'] = 'G'
            user = Tuser.objects.get(id=userID)
            # Group ID
            group = user.allgroups_set.all().first()
            res['group_id'] = group.id
            groupManagers = group.groupManagers.all()
            groupManagersIDs = []
            for groupManager in groupManagers:
                groupManagersIDs.append(groupManager.id)
            companies_group = TCompany.objects.filter(group_id=res['group_id'])
            companies = []
            for company_id in companies_group:
                companies.append(company_id.id)
            res['companies'] = companies
            res['groupManagers'] = groupManagersIDs
        except AttributeError as ae:
            resp = code.get_msg(code.PERMISSION_DENIED)
        print json.dumps(res)
        return json.dumps(res)

def getGroupByCompanyManagerID(loginType, userID):
    res = {}
    # Company Manager
    if (loginType == 3):
        # Company Manager
        res['login_type'] = 'C'
        user = Tuser.objects.get(id=userID)
        # Company ID
        company_id = user.tcompany.id
        # Group ID
        groupID = TCompany.objects.get(id=company_id).group.id
        companies = []
        companies.append(company_id)
        # Companies Lists
        res['companies'] = companies
        res['group_id'] = groupID
    print json.dumps(res)
    return json.dumps(res)