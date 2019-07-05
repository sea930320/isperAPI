#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import random
from account.models import *
from group.models import *
from django.db.models import Q
from group.models import AllGroups
from account.models import LoginLog
from project.models import Project
import json
import code
import itertools

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
    try:
        user = Tuser.objects.get(id=userID)
        if loginType == 2:
            res['login_type'] = 'G'
            group = user.allgroups_set.all().first()
        elif loginType == 6:
            res['login_type'] = 'GA'
            group = user.allgroups_set_assistants.all().first()
        else:
            return False
        res['group_id'] = group.id
        groupManagers = group.groupManagers.all()
        groupManagerAssistants = group.groupManagerAssistants.all()
        groupManagersIDs = []
        groupManagerAssistantsIDs = []
        for groupManager in groupManagers:
            groupManagersIDs.append(groupManager.id)
        for groupManagerAssistant in groupManagerAssistants:
            groupManagerAssistantsIDs.append(groupManagerAssistant.id)
        companies_group = TCompany.objects.filter(group_id=res['group_id'])
        companies = []
        for company_id in companies_group:
            companies.append(company_id.id)
        res['companies'] = companies
        res['groupManagers'] = groupManagersIDs
        res['groupManagerAssistants'] = groupManagersIDs
    except AttributeError as ae:
        resp = code.get_msg(code.PERMISSION_DENIED)
    return json.dumps(res)


def getGroupByCompanyManagerID(loginType, userID):
    res = {}
    user = Tuser.objects.get(id=userID)
    if loginType == 3:
        res['login_type'] = 'C'
        company_id = user.tcompanymanagers_set.get().tcompany.id
    elif loginType == 7:
        res['login_type'] = 'CA'
        company_id = user.t_company_set_assistants.all().first().id
    else:
        return False
    # Group ID
    groupID = TCompany.objects.get(id=company_id).group.id
    companies = []
    companies.append(company_id)
    # Companies Lists
    res['companies'] = companies
    res['group_id'] = groupID
    return json.dumps(res)


def loginLog(loginType, userID, ip):
    user = Tuser.objects.get(id=userID)
    role = user.roles.get(pk=loginType)

    group = None
    company = None
    if loginType == 1:
        pass
    elif loginType == 2:
        group = user.allgroups_set.all().first()
    elif loginType == 6:
        group = user.allgroups_set_assistants.all().first()
    elif loginType == 3:
        company_id = user.tcompanymanagers_set.get().tcompany.id
        company = TCompany.objects.get(pk=company_id)
        group = company.group
    elif loginType == 7:
        company = user.t_company_set_assistants.all().first()
        if company is not None:
            group = company.group
    elif loginType == 4:
        group = user.allgroups_set_instructors.all().first()
    elif loginType == 8:
        group = user.allgroups_set_instructor_assistants.all().first()
    else:
        company = user.tcompany
        if company is not None:
            group = company.group
    login_log = LoginLog(user=user, role=role, group=group, company=company, login_ip=ip)
    login_log.save()


def getProjectIDByGroupManager(userID):

    gruopID = AllGroups.objects.get(groupManagers__in=[Tuser.objects.get(id=userID)])
    groupInfo = AllGroups.objects.filter(groupManagers__in=[Tuser.objects.get(id=userID)])
    companyAndAssist = TCompany.objects.filter(group=gruopID).values('tcompanymanagers__tuser_id', 'assistants')
    allData = list(groupInfo.values('groupManagerAssistants', 'groupManagers')) + list(companyAndAssist)
    allID = itertools.chain.from_iterable(map(lambda x: x.values(), allData))

    return list(Project.objects.filter(created_by__in=list(allID)).values_list('id', flat=True))


def getProjectIDByGroupManagerAssistant(userID):

    gruopID = AllGroups.objects.get(groupManagerAssistants__in=[Tuser.objects.get(id=userID)])
    groupInfo = AllGroups.objects.filter(groupManagerAssistants__in=[Tuser.objects.get(id=userID)])
    companyAndAssist = TCompany.objects.filter(group=gruopID).values('tcompanymanagers__tuser_id', 'assistants')
    allData = list(groupInfo.values('groupManagerAssistants', 'groupManagers')) + list(companyAndAssist)
    allID = itertools.chain.from_iterable(map(lambda x: x.values(), allData))

    return list(Project.objects.filter(created_by__in=list(allID)).values_list('id', flat=True))


def getProjectIDByCompanyManager(userID):

    companyID = TCompanyManagers.objects.get(tuser_id=userID).tcompany_id
    cM = list(itertools.chain.from_iterable(map(lambda x: x.values(), list(TCompany.objects.filter(pk=companyID).values('tcompanymanagers__tuser_id')))))
    cMA = list(itertools.chain.from_iterable(map(lambda x: x.values(), list(TCompany.objects.filter(pk=companyID).values('assistants')))))

    return list(Project.objects.filter(Q(created_by_id__in=cM, created_role_id=3) | Q(created_by_id__in=cMA, created_role_id=7)).values_list('id', flat=True))


def getProjectIDByCompanyManagerAssistant(userID):

    companyID = TCompanyManagerAssistants.objects.get(tuser_id=userID).tcompany_id
    cM = list(itertools.chain.from_iterable(map(lambda x: x.values(), list(TCompany.objects.filter(pk=companyID).values('tcompanymanagers__tuser_id')))))
    cMA = list(itertools.chain.from_iterable(map(lambda x: x.values(), list(TCompany.objects.filter(pk=companyID).values('assistants')))))

    return list(Project.objects.filter(Q(created_by_id__in=cM, created_role_id=3) | Q(created_by_id__in=cMA, created_role_id=7)).values_list('id', flat=True))
