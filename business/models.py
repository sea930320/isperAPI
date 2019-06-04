#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from project.models import Project
from account.models import Tuser, TJobType
from project.models import ProjectRoleAllocation
from workflow.models import FlowNode

def get_business_doc_upload_to(instance, filename):
    return u'business/{}/{}'.format(instance.experiment_id, filename)

# 实验任务
class Business(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'名称')
    huanxin_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'环信id')
    project = models.ForeignKey(Project, verbose_name=u'项目')
    show_nickname = models.BooleanField(default=False, verbose_name=u'昵称显示组员')
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')
    status = models.PositiveIntegerField(default=1, choices=const.BUSINESS_STATUS, verbose_name=u'状态')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    node = models.ForeignKey(FlowNode, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=u'当前环节')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前路径')
    cur_project_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前项目')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    finish_time = models.DateTimeField(blank=True, null=True, verbose_name=u'实际完成时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_business"
        ordering = ('-create_time', )
        verbose_name_plural = verbose_name = u"Business"

    def __unicode__(self):
        return self.name

# 项目角色
class BusinessRole(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    name = models.CharField(max_length=32, verbose_name=u'角色名称')
    type = models.CharField(max_length=28, verbose_name=u'角色类型')
    image_id = models.IntegerField(verbose_name=u'角色形象', null=True)
    category = models.PositiveIntegerField(verbose_name=u'类别', null=True)
    capacity = models.IntegerField(verbose_name=u'人数', default=1)
    flow_role_id = models.IntegerField(verbose_name=u'流程角色id')
    project_role_id = models.IntegerField(verbose_name=u'Project Role Id')
    job_type = models.ForeignKey(TJobType, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "t_business_role"
        verbose_name_plural = verbose_name = u"BusinessRole"

    def __unicode__(self):
        return self.name

# 项目角色分配
class BusinessRoleAllocation(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    role = models.ForeignKey(BusinessRole, on_delete=models.CASCADE, verbose_name=u'角色')
    can_terminate = models.BooleanField(verbose_name=u'结束环节权限')
    can_brought = models.BooleanField(verbose_name=u'是否被带入')
    can_take_in = models.BooleanField(verbose_name=u'This guy will be taken in this step ', default=False)
    can_start = models.BooleanField(verbose_name=u'Can Start the business', default=False)
    no = models.IntegerField(default=1, verbose_name=u'Number')

    class Meta:
        db_table = "t_business_role_allocation"
        verbose_name_plural = verbose_name = u"Business Role Allocation"

    def __unicode__(self):
        return self.business.name

class BusinessTeam(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'User')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    class Meta:
        db_table = "t_business_team"
        ordering = ('-create_time', )
        verbose_name_plural = verbose_name = u"BusinessTeam"

    def __unicode__(self):
        return self.name

class BusinessDoc(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    filename = models.CharField(max_length=64, verbose_name=u'名称')
    file = models.FileField(upload_to=get_business_doc_upload_to, storage=FileStorage(), verbose_name=u'文件')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    type = models.IntegerField(blank=True, null=True, verbose_name=u'文件类型')
    content = models.TextField(blank=True, null=True, verbose_name=u'内容')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    sign = models.CharField(max_length=12, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.BooleanField(default=False, verbose_name=u'签名状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = "t_business_doc"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"BusinessDoc"

    def __unicode__(self):
        return self.filename

class BusinessDocTeam(models.Model):
    business_team = models.ForeignKey(BusinessTeam, on_delete=models.CASCADE, verbose_name=u'Business')
    business_doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    class Meta:
        db_table = "t_business_doc_team"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"BusinessDocTeam"
    def __unicode__(self):
        return u''