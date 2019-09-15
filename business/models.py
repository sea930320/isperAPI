#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from project.models import Project, ProjectDoc
from account.models import Tuser, TJobType, OfficeItems, TCompany, TParts, TRole
from project.models import ProjectRoleAllocation
from group.models import *
from workflow.models import FlowNode, SelectDecideItem
from system.models import UploadFile


def get_business_doc_upload_to(instance, filename):
    return u'business/{}/{}'.format(instance.business_id, filename)


# 实验流转路径
class BusinessParallelNodes(models.Model):
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'当前环节')
    is_done = models.IntegerField(default=0, verbose_name=u'node_done_status')

    class Meta:
        db_table = "t_business_parallel_node"
        verbose_name_plural = verbose_name = u"business_parallel_node"

    def __unicode__(self):
        return str(self.node_id)


class BusinessParallelPassedNodes(models.Model):
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'当前环节')

    class Meta:
        db_table = "t_business_parallel_passed_node"
        verbose_name_plural = verbose_name = u"business_parallel_passed_node"

    def __unicode__(self):
        return str(self.node_id)


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
    jumper_id = models.IntegerField(verbose_name=u'当前项目', null=True, default=None)
    parallel_nodes = models.ManyToManyField(BusinessParallelNodes)
    parallel_passed_nodes = models.ManyToManyField(BusinessParallelPassedNodes)
    parallel_count = models.IntegerField(verbose_name=u'parallel count', null=True, default=0)

    class Meta:
        db_table = "t_business"
        ordering = ('-create_time',)
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
        return self.task_id


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
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, blank=True, null=True, on_delete=models.CASCADE, verbose_name=u'实验路径')
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
        return self.business.name


# 实验环节占位状态
class BusinessPositionStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'任务')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, blank=True, null=True,
                                                 on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, blank=True, null=True, on_delete=models.CASCADE, verbose_name=u'实验路径')
    position_id = models.IntegerField(verbose_name=u'占位')
    sitting_status = models.PositiveIntegerField(choices=const.SITTING_STATUS, default=1, verbose_name=u'入席退席状态')

    class Meta:
        db_table = "t_business_position_status"
        verbose_name_plural = verbose_name = u"实验任务场景占位状态"

    def __unicode__(self):
        return str(self.sitting_status)


# 实验心得
class BusinessExperience(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'实验')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    content = models.TextField(verbose_name=u'心得')
    status = models.PositiveSmallIntegerField(choices=const.SUBMIT_STATUS, default=1, verbose_name=u'提交状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_business_experience"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"实验心得"

    def __unicode__(self):
        return u""


class BusinessReportStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation')
    path = models.ForeignKey(BusinessTransPath, blank=True, null=True, on_delete=models.CASCADE, verbose_name=u'实验路径')
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
    user = models.ForeignKey(Tuser, blank=True, null=True, on_delete=models.CASCADE, verbose_name=u'User')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    no = models.IntegerField(default=1, verbose_name=u'Number')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_business_team_member"
        ordering = ('-create_time',)
        verbose_name_plural = verbose_name = u"BusinessTeam"

    def __unicode__(self):
        return str(self.id)


# 消息
class BusinessMessage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'User')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation')
    file_id = models.IntegerField(blank=True, null=True, verbose_name=u'文件')
    path = models.ForeignKey(BusinessTransPath, on_delete=models.CASCADE, verbose_name=u'实验路径')
    user_name = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'姓名')
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
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation', blank=True, null=True,
                                                 default=None)
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
    doc = models.ForeignKey(ProjectDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc', null=True)
    name = models.CharField(max_length=64, verbose_name=u'模板名称')
    content = models.TextField(verbose_name=u'内容')
    file = models.FileField(upload_to=get_business_doc_upload_to, storage=FileStorage(),
                            blank=True, null=True, verbose_name=u'文件')
    sign = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.PositiveIntegerField(choices=const.SIGN_STATUS, default=0, verbose_name=u'签名状态')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation', blank=True, null=True,
                                                 default=None)
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
    doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,
                                                 verbose_name=u'Business Role Allocation', blank=True, null=True,
                                                 default=None)
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


class BusinessPost(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    name = models.CharField(max_length=64, verbose_name=u'名称')
    content = models.TextField(verbose_name=u'内容', blank=True, null=True)
    docx_id = models.IntegerField(blank=True, null=True, verbose_name=u'文件路径1')
    html_id = models.IntegerField(blank=True, null=True, verbose_name=u'文件路径2')
    file_type = models.CharField(max_length=10, verbose_name=u'文件类型')
    created_by = models.ForeignKey(Tuser, models.CASCADE, verbose_name=u'创建者')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = "t_business_post"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"公告"

    def __unicode__(self):
        return self.name


# added by ser
class BusinessStepStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    step = models.IntegerField(default=1, verbose_name=u'步骤')

    class Meta:
        db_table = "t_business_step_status"
        verbose_name_plural = verbose_name = u"BusinessStepStatus"

    def __unicode__(self):
        return self.name


class BusinessDocTeamStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    business_team_member = models.ForeignKey(BusinessTeamMember, on_delete=models.CASCADE, verbose_name=u'Business')
    business_doc = models.ForeignKey(BusinessDoc, on_delete=models.CASCADE, verbose_name=u'BusinessDoc')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'环节')
    permission = models.IntegerField(default=1, verbose_name=u'Permission')
    status = models.IntegerField(default=0, verbose_name=u'Status')

    class Meta:
        db_table = "t_business_doc_team_status"
        verbose_name_plural = verbose_name = u"BusinessDocTeamStatus"

    def __unicode__(self):
        return u''


class SelectDecideResult(models.Model):
    business_role_allocation = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE, verbose_name=u'Business Role Allocation')
    selectedItems = models.ManyToManyField(SelectDecideItem, verbose_name=u'Selected Items')

    class Meta:
        db_table = "t_selectDecideResult"
        verbose_name_plural = verbose_name = u"selectDecideResult"

    def __unicode__(self):
        return u''


class VoteItem(models.Model):
    content = models.TextField(verbose_name=u'Vote Content')
    voted_count = models.IntegerField(default=0, verbose_name=u'Vote Count')
    voted_users = models.ManyToManyField(Tuser, verbose_name=u'Voted Users')

    class Meta:
        db_table = "t_voteItem"
        verbose_name_plural = verbose_name = u"voteItem"

    def __unicode__(self):
        return self.content


class VoteMember(models.Model):
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Vote User ID')
    voted = models.IntegerField(default=0, verbose_name=u'Vote Done')

    class Meta:
        db_table = "t_voteMember"
        verbose_name_plural = verbose_name = u"voteMember"

    def __unicode__(self):
        return str(self.pk)


class Vote(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business ID')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'Node ID')
    mode = models.IntegerField(verbose_name=u'Vote Mode')
    title = models.TextField(verbose_name=u'Vote Title')
    description = models.TextField(verbose_name=u'Vote Description')
    method = models.IntegerField(blank=True, null=True, verbose_name=u'Vote Method')
    end_time = models.DateTimeField(verbose_name=u'Vote End Time')
    max_vote = models.IntegerField(blank=True, null=True, verbose_name=u'Vote Max Count')
    lost_vote = models.IntegerField(blank=True, null=True, verbose_name=u'Vote Lost Count')
    items = models.ManyToManyField(VoteItem, verbose_name=u'Vote Items')
    members = models.ManyToManyField(VoteMember, verbose_name=u'Vote Members')

    class Meta:
        db_table = "t_vote"
        verbose_name_plural = verbose_name = u"vote"

    def __unicode__(self):
        return self.title


class BusinessProjectTrack(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
    process_type = models.IntegerField(verbose_name=u'Process Type', null=True)
    flow_trans_id = models.IntegerField(verbose_name=u'TFlowTrans ID', null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = "t_business_project_track"
        ordering = ('-create_time',)
        verbose_name_plural = verbose_name = u"BusinessProjectTrack"

    def __unicode__(self):
        return str(self.id)


class PollMember(models.Model):
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Poll User ID')
    poll_status = models.IntegerField(default=0, verbose_name=u'Poll status')

    class Meta:
        db_table = "t_pollMember"
        verbose_name_plural = verbose_name = u"pollMember"

    def __unicode__(self):
        return str(self.pk)


class Poll(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business ID')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'Node ID')
    title = models.TextField(verbose_name=u'投票主题')
    method = models.IntegerField(blank=True, null=True, verbose_name=u'投票方式')
    end_time = models.DateTimeField(verbose_name=u'投票用时')
    share = models.IntegerField(blank=True, null=True, verbose_name=u'投票结果')
    members = models.ManyToManyField(PollMember, verbose_name=u'投票人范围')

    class Meta:
        db_table = "t_poll"
        verbose_name_plural = verbose_name = u"poll"

    def __unicode__(self):
        return self.title


class BusinessSurvey(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    project_id = models.IntegerField(verbose_name=u'当前项目', null=True)
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, verbose_name=u'Node ID')
    title = models.TextField(verbose_name=u'Survey Title')
    description = models.TextField(verbose_name=u'Survey Description')
    step = models.IntegerField(default=0, verbose_name=u'Survey Step')
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')
    end_quote = models.TextField(verbose_name=u'Survey End Quotion')
    target = models.IntegerField(default=0, verbose_name=u'Survey Target', choices=const.BUSINESS_SURVEY_TARGET)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'Create Time')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'Update Time')
    is_ended = models.BooleanField(default=False, verbose_name=u'is survey ended')

    class Meta:
        db_table = "t_business_survey"
        verbose_name_plural = verbose_name = u"t_business_surveys"

    def __unicode__(self):
        return self.title


class BusinessQuestion(models.Model):
    survey = models.ForeignKey(BusinessSurvey, on_delete=models.CASCADE, verbose_name=u'Business Survey')
    type = models.IntegerField(default=0, verbose_name=u'Question Type', choices=const.BUSINESS_QUESTION_TYPE)
    select_option = models.IntegerField(null=True, blank=True, verbose_name=u'Question Type')
    title = models.TextField(verbose_name=u'Question Title')
    description = models.TextField(verbose_name=u'Question Description')

    class Meta:
        db_table = "t_business_question"
        verbose_name_plural = verbose_name = u"t_business_questions"

    def __unicode__(self):
        return self.title


class BusinessQuestionCase(models.Model):
    question = models.ForeignKey(BusinessQuestion, on_delete=models.CASCADE, verbose_name=u'Business Question')
    case = models.TextField(verbose_name=u'Question Case Option')

    class Meta:
        db_table = "t_business_question_case"
        verbose_name_plural = verbose_name = u"t_business_question_cases"

    def __unicode__(self):
        return self.case


class BusinessSurveyAnsweredUser(models.Model):
    survey = models.ForeignKey(BusinessSurvey, on_delete=models.CASCADE, verbose_name=u'Business Survey')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者', null=True, default=None)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'Create Time')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'Update Time')

    class Meta:
        db_table = "t_business_survey_answered_user"
        verbose_name_plural = verbose_name = u"t_business_survey_answered_users"

    def __unicode__(self):
        return self.id


class BusinessAnswer(models.Model):
    survey = models.ForeignKey(BusinessSurvey, on_delete=models.CASCADE, verbose_name=u'Business Survey')
    question = models.ForeignKey(BusinessQuestion, on_delete=models.CASCADE, verbose_name=u'Business Question')
    answer = models.TextField(verbose_name=u'Business Answer')
    question_title = models.TextField(verbose_name=u'Question Title', default='')
    question_cases = models.ManyToManyField(BusinessQuestionCase, verbose_name=u'Qustion Case Answer')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者', null=True, default=None)
    answeredUser = models.ForeignKey(BusinessSurveyAnsweredUser, on_delete=models.CASCADE, verbose_name=u'Answered User', null=True, default=None)

    class Meta:
        db_table = "t_business_answer"
        verbose_name_plural = verbose_name = u"t_business_answers"

    def __unicode__(self):
        return self.id


class BusinessGuide(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    guider = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Guider', related_name="guider_set")
    request = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Request', related_name="request_set")
    role = models.ForeignKey(TRole, on_delete=models.CASCADE, verbose_name=u'Role')
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "t_business_guider"
        verbose_name_plural = verbose_name = u"t_business_guider"

    def __unicode__(self):
        return self.id


class GuideChatLog(models.Model):
    guide = models.ForeignKey(BusinessGuide, on_delete=models.CASCADE, verbose_name=u'Guide')
    msg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'消息内容')
    sender = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Tuser')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_guide_chatlog"
        verbose_name_plural = verbose_name = u"GuideChatLog"

    def __unicode__(self):
        return str(self.guide_id)


class BusinessAsk(models.Model):
    office = models.ForeignKey(OfficeItems, on_delete=models.CASCADE, verbose_name=u'Office')
    group = models.ForeignKey(AllGroups, on_delete=models.CASCADE, verbose_name=u'Group')
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "t_business_ask"
        verbose_name_plural = verbose_name = u"t_business_ask"

    def __unicode__(self):
        return self.id


class AskChatLog(models.Model):
    ask = models.ForeignKey(BusinessAsk, on_delete=models.CASCADE, verbose_name=u'Ask')
    msg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'消息内容')
    sender = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Tuser')
    sender_role = models.ForeignKey(TRole, on_delete=models.CASCADE, verbose_name=u'Sender Role')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_ask_chatlog"
        verbose_name_plural = verbose_name = u"AskChatLog"

    def __unicode__(self):
        return str(self.ask_id)


class BusinessEvaluation(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE,  blank=True, null=True, verbose_name=u'business')
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE,  blank=True, null=True, verbose_name=u'user')
    role_alloc = models.ForeignKey(BusinessRoleAllocation, on_delete=models.CASCADE,  blank=True, null=True, verbose_name=u'role_alloc')
    comment = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'comment')
    value = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'value')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_business_evaluation"
        verbose_name_plural = verbose_name = u"BusinessEvaluation"

    def __unicode__(self):
        return str(self.pk)

############################################################################################################
class BusinessBillList(models.Model):
    bill_name = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'bill_name')
    business = models.ForeignKey(Business, on_delete=models.CASCADE,  blank=True, null=True, verbose_name=u'business')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    edit_mode = models.IntegerField(blank=True, null=True, verbose_name=u'edit_mode')
    chapters = models.ManyToManyField('BusinessBillChapter', blank=True,
                                  verbose_name=u'chapters')
    part_mode_parts = models.ManyToManyField('BusinessBillPartPartMode', blank=True,
                                  verbose_name=u'part_mode_parts')
    docs = models.ManyToManyField('BusinessBillDoc', blank=True,
                                  verbose_name=u'docs')

    class Meta:
        db_table = "t_business_bill_list"
        verbose_name_plural = verbose_name = u"BusinessBillList"

    def __unicode__(self):
        return str(self.pk)

class BusinessBillChapter(models.Model):
    chapter_number = models.IntegerField(blank=True, null=True, verbose_name=u'bill_chapter')
    chapter_title = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'chapter_title')
    chapter_content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'chapter_content')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    sections = models.ManyToManyField('BusinessBillSection', blank=True,
                                     verbose_name=u'sections')


    class Meta:
        db_table = "t_business_bill_chapter"
        verbose_name_plural = verbose_name = u"BusinessBillChapter"

    def __unicode__(self):
        return str(self.pk)

class BusinessBillSection(models.Model):
    section_number = models.IntegerField(blank=True, null=True, verbose_name=u'section_number')
    section_title = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'section_title')
    section_content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'section_content')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    parts = models.ManyToManyField('BusinessBillPart', blank=True,
                                     verbose_name=u'parts')

    class Meta:
        db_table = "t_business_bill_section"
        verbose_name_plural = verbose_name = u"BusinessBillSection"

    def __unicode__(self):
        return str(self.pk)

class BusinessBillPart(models.Model):
    part_number = models.IntegerField(blank=True, null=True, verbose_name=u'part_number')
    part_title = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_title')
    part_content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_content')
    part_reason = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_reason')
    doc_id = models.IntegerField(blank=True, null=True, verbose_name=u'doc_id')
    doc_conception = models.IntegerField(blank=True, null=True, verbose_name=u'doc_conception')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    part_docs = models.ManyToManyField('BusinessBillPartDoc', blank=True,
                                  verbose_name=u'part_docs')

    class Meta:
        db_table = "t_business_bill_part"
        verbose_name_plural = verbose_name = u"BusinessBillPart"

    def __unicode__(self):
        return str(self.pk)


class BusinessBillPartDoc(models.Model):
    doc = models.ForeignKey(UploadFile, null=True, on_delete=models.CASCADE, verbose_name=u'doc_id')
    doc_conception = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_conception')
    doc_name = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_name')
    doc_url = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_url')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_business_bill_part_doc"
        verbose_name_plural = verbose_name = u"BusinessBillPartDoc"

    def __unicode__(self):
        return str(self.pk)


class BusinessBillPartPartMode(models.Model):
    part_number = models.IntegerField(blank=True, null=True, verbose_name=u'part_number')
    part_title = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_title')
    part_content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_content')
    part_reason = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'part_reason')
    doc_id = models.IntegerField(blank=True, null=True, verbose_name=u'doc_id')
    doc_conception = models.IntegerField(blank=True, null=True, verbose_name=u'doc_conception')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    part_docs = models.ManyToManyField('BusinessBillPartDoc', blank=True,
                                       verbose_name=u'part_docs')

    class Meta:
        db_table = "t_business_bill_part_part_mode"
        verbose_name_plural = verbose_name = u"BusinessBillPartPartMode"

    def __unicode__(self):
        return str(self.pk)


class BusinessBillDoc(models.Model):
    doc = models.ForeignKey(UploadFile, null=True, on_delete=models.CASCADE, verbose_name=u'doc_id')
    doc_conception = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_conception')
    doc_name = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_name')
    doc_url = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'doc_url')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_business_bill_doc"
        verbose_name_plural = verbose_name = u"BusinessBillDoc"

    def __unicode__(self):
        return str(self.pk)