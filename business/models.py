#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from project.models import Project
from account.models import Tuser, TJobType, OfficeItems, TCompany, TParts
from project.models import ProjectRoleAllocation
from workflow.models import FlowNode


def get_business_doc_upload_to(instance, filename):
    return u'business/{}/{}'.format(instance.experiment_id, filename)


# 实验任务
class Business(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'名称')
    huanxin_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'环信id')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
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
    officeItem = models.ForeignKey(OfficeItems, blank=True, null=True, on_delete=models.CASCADE)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    target_company = models.ForeignKey(TCompany, blank=True, null=True, on_delete=models.CASCADE)
    target_part = models.ForeignKey(TParts, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = "t_business"
        ordering = ('-create_time', )
        verbose_name_plural = verbose_name = u"Business"

    def __unicode__(self):
        return self.name


# 实验流转路径
class BusinessTransPath(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'当前环节')
    task_id = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'xml中task id')
    step = models.IntegerField(default=1, blank=True, null=True, verbose_name=u'步骤')
    control_status = models.PositiveIntegerField(default=1, choices=const.EXPERIMENT_CONTROL_STATUS,
                                                 verbose_name=u'表达管理状态')
    vote_status = models.PositiveIntegerField(choices=const.EXPERIMENT_VOTE_STATUS, default=1, verbose_name=u'投票状态')

    class Meta:
        db_table = "t_business_trans_path"
        ordering = ['step']
        verbose_name_plural = verbose_name = u"实验流转路径"

    def __unicode__(self):
        return self.business_id


# 项目角色
class BusinessRole(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
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
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
    project_role_alloc_id = models.IntegerField(verbose_name=u'ProjectRoleAlloction ID', null=True)
    flow_role_alloc_id = models.IntegerField(verbose_name=u'FlowRoleAlloction ID', null=True)
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


# 实验环节角色状态
class BusinessRoleAllocationStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    speak_times = models.IntegerField(default=0, verbose_name=u'发言次数')
    submit_status = models.PositiveIntegerField(choices=const.SUBMIT_STATUS, default=9, verbose_name=u'提交状态')
    show_status = models.PositiveIntegerField(choices=const.SHOW_STATUS, default=9, verbose_name=u'展示状态')
    come_status = models.PositiveIntegerField(choices=const.COME_STATUS, default=9, verbose_name=u'带入带出状态')
    sitting_status = models.PositiveIntegerField(choices=const.SITTING_STATUS, default=1, verbose_name=u'入席退席状态')
    stand_status = models.PositiveIntegerField(choices=const.STAND_STATUS, default=2, verbose_name=u'起立坐下状态')
    vote_status = models.PositiveIntegerField(choices=const.VOTE_STATUS, default=0, verbose_name=u'投票状态')

    class Meta:
        db_table = "t_business_role_allocation_status"
        verbose_name_plural = verbose_name = u"实验环节角色状态"

    def __unicode__(self):
        return u""

# 实验环节占位状态
class BusinessPositionStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    position_id = models.IntegerField(verbose_name=u'占位')
    sitting_status = models.PositiveIntegerField(choices=const.SITTING_STATUS, default=1, verbose_name=u'入席退席状态')

    class Meta:
        db_table = "t_business_position_status"
        verbose_name_plural = verbose_name = u"实验任务场景占位状态"

    def __unicode__(self):
        return u""

class BusinessReportStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    position_id = models.IntegerField(verbose_name=u'占位')
    schedule_status = models.PositiveIntegerField(choices=const.SCHEDULE_STATUS, default=1, verbose_name=u'安排状态')

    class Meta:
        db_table = "t_business_report_status"
        verbose_name_plural = verbose_name = u"实验任务场景报告状态"

    def __unicode__(self):
        return u""

class BusinessTeamMember(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
    business_role = models.ForeignKey(BusinessRole, on_delete=models.CASCADE, verbose_name=u'Business Role')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'User')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    no = models.IntegerField(default=1, verbose_name=u'Number')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    class Meta:
        db_table = "t_business_team_member"
        ordering = ('-create_time', )
        verbose_name_plural = verbose_name = u"BusinessTeam"

    def __unicode__(self):
        return self.name
# 消息
class BusinessMessage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'User')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    file_id = models.IntegerField(blank=True, null=True, verbose_name=u'文件')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    user_name = models.CharField(max_length=8, blank=True, null=True, verbose_name=u'姓名')
    role_name = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'角色名称')
    msg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'消息内容')
    msg_type = models.CharField(max_length=10, verbose_name=u'消息类型')
    ext = models.TextField(verbose_name=u'自定义拓展属性')
    opt_status = models.BooleanField(default=False, verbose_name=u'操作状态')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=u'消息发送时间')

    class Meta:
        db_table = "t_business_message"
        verbose_name_plural = verbose_name = u"消息"

    def __unicode__(self):
        return u""

# 消息文件
class BusinessMessageFile(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'User')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    file = models.FileField(upload_to=get_business_doc_upload_to, storage=FileStorage(), verbose_name=u'文件')
    length = models.PositiveIntegerField(blank=True, null=True, verbose_name=u'语音时长', help_text=u'单位为秒，这个属性只有语音消息有')
    url = models.CharField(max_length=100, blank=True, null=True, verbose_name=u'图片语音等文件的网络URL',
                           help_text=u'图片和语音消息有这个属性')
    filename = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'文件名称', help_text=u'图片和语音消息有这个属性')
    secret = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'获取文件的secret',
                              help_text=u'图片和语音消息有这个属性')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 't_business_message_file'
        verbose_name_plural = verbose_name = u'消息文件'

    def __unicode__(self):
        return self.file.name

class BusinessDoc(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前路径')
    filename = models.CharField(max_length=64, verbose_name=u'名称')
    file = models.FileField(upload_to=get_business_doc_upload_to, storage=FileStorage(), verbose_name=u'文件')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    type = models.IntegerField(blank=True, null=True, verbose_name=u'文件类型')
    content = models.TextField(blank=True, null=True, verbose_name=u'内容')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation', blank=True, null=True, default=None)
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

# 用户编辑模版内容
class BusinessDocContent(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    name = models.CharField(max_length=64, verbose_name=u'模板名称')
    content = models.TextField(verbose_name=u'内容')
    file = models.FileField(upload_to=get_business_doc_upload_to, storage=FileStorage(),
                            blank=True, null=True, verbose_name=u'文件')
    sign = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.PositiveIntegerField(choices=const.SIGN_STATUS, default=0, verbose_name=u'签名状态')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation', blank=True, null=True, default=None)
    has_edited = models.BooleanField(default=False, verbose_name=u'是否已编辑')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_business_doc_content"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"用户编辑模版内容"

    def __unicode__(self):
        return self.name

class BusinessDocTeam(models.Model):
    business_team_member = models.ForeignKey(BusinessTeamMember, on_delete=models.CASCADE, verbose_name=u'Business')
    business_doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    class Meta:
        db_table = "t_business_doc_team"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"BusinessDocTeam"
    def __unicode__(self):
        return u''

# 实验环节文档签字记录
class BusinessDocSign(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation', blank=True, null=True, default=None)
    sign = models.CharField(max_length=18, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.PositiveIntegerField(choices=const.SIGN_STATUS, default=0, verbose_name=u'签名状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = "t_business_doc_sign"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"实验环节文档签字记录"

    def __unicode__(self):
        return u""



# 实验环节笔记
class BusinessNotes(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    content = models.TextField(verbose_name=u'内容')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_business_notes"
        verbose_name_plural = verbose_name = u"实验环节笔记"

    def __unicode__(self):
        return u""