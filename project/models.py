#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from account.models import Tuser, TJobType, TParts, TCourse, TRole, OfficeItems
from workflow.models import FlowNode


# 实验项目
class Project(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    name = models.CharField(max_length=64, verbose_name=u'名称')#
    all_role = models.PositiveIntegerField(default=1, choices=const.PROJECT_ALL_ROLE, verbose_name=u'允许一人扮演所有角色')
    course = models.ForeignKey(TCourse, verbose_name=u'课程')
    reference = models.PositiveIntegerField(default=1, choices=const.PROJECT_REFERENCE, verbose_name=u'成果参考释放方式')
    public_status = models.PositiveIntegerField(default=1, choices=const.PROJECT_PUBLIC, verbose_name=u'申请为公共项目状态')
    level = models.PositiveIntegerField(default=1, choices=const.PROJECT_LEVEL, verbose_name=u'实验层次')
    entire_graph = models.PositiveIntegerField(default=1, choices=const.PROJECT_ENTIRE_GRAPH, verbose_name=u'流程图完整显示')
    type = models.PositiveIntegerField(default=1, choices=const.EXPERIMENT_TYPE, verbose_name=u'实验类型')
    can_redo = models.PositiveIntegerField(default=1, choices=const.PROJECT_CAN_REDO, verbose_name=u'是否允许重做')
    is_open = models.PositiveIntegerField(default=1, choices=const.PROJECT_IS_OPEN, verbose_name=u'开放模式')
    target_users = models.ManyToManyField(Tuser, related_name='projectOpenTargeted_users')
    target_parts = models.ForeignKey(TParts, blank=True, null=True, on_delete=models.CASCADE, related_name='projectTargetPart_set')
    officeItem = models.ForeignKey(OfficeItems, blank=True, null=True, on_delete=models.CASCADE)
    ability_target = models.PositiveIntegerField(default=1, choices=const.PROJECT_ABILITY_TARGET, verbose_name=u'能力目标')
    start_time = models.DateField(blank=True, null=True, verbose_name=u'开放开始时间')
    end_time = models.DateField(blank=True, null=True, verbose_name=u'开放结束时间')
    intro = models.TextField(verbose_name=u'项目简介')
    purpose = models.TextField(verbose_name=u'实验目的')
    requirement = models.TextField(verbose_name=u'实验要求')
    step = models.IntegerField(default=const.PRO_STEP_0, verbose_name=u'设置步骤')
    created_by = models.ForeignKey(Tuser, models.CASCADE, verbose_name=u'创建者', related_name='projectCreator_set')
    created_role = models.ForeignKey(TRole, models.CASCADE, verbose_name=u'创建者_ROLE')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    protected = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否保护')
    is_group_share = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否共享')
    is_company_share = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否集群共享')
    use_to = models.ForeignKey(TParts, blank=True, null=True, on_delete=models.CASCADE, related_name='projectUseTo_set')

    class Meta:
        db_table = "t_project"
        ordering = ['-create_time', '-update_time']
        verbose_name_plural = verbose_name = u"实验项目"

    def __unicode__(self):
        return self.name

class ProjectNodeInfo(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE)
    look_on = models.BooleanField(verbose_name=u'Look On')
    class Meta:
        db_table = "t_project_node_info"

    def __unicode__(self):
        return self.project.name + self.node.name


# 项目角色
class ProjectRole(models.Model):
    project_id = models.IntegerField(verbose_name=u'项目')
    flow_role_id = models.IntegerField(verbose_name=u'流程角色id')
    image_id = models.IntegerField(verbose_name=u'角色形象', null=True)
    name = models.CharField(max_length=32, verbose_name=u'角色名称')
    type = models.CharField(max_length=28, verbose_name=u'角色类型')
    min = models.IntegerField(default=1, verbose_name=u'最小人数', null=True)
    max = models.IntegerField(default=100, verbose_name=u'最大人数', null=True)
    category = models.PositiveIntegerField(verbose_name=u'类别', null=True)
    capacity = models.IntegerField(verbose_name=u'人数', default=1)
    job_type = models.ForeignKey(TJobType, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        db_table = "t_project_role"
        verbose_name_plural = verbose_name = u"项目角色"

    def __unicode__(self):
        return self.name


# 项目角色分配
class ProjectRoleAllocation(models.Model):
    project_id = models.IntegerField(verbose_name=u'流程')
    node_id = models.IntegerField(verbose_name=u'环节')
    role_id = models.IntegerField(verbose_name=u'角色')
    can_terminate = models.BooleanField(verbose_name=u'结束环节权限')
    can_brought = models.BooleanField(verbose_name=u'是否被带入')
    can_take_in = models.BooleanField(verbose_name=u'This guy will be taken in this step ', default=False)
    can_start = models.BooleanField(verbose_name=u'Can Start the business', default=False)
    num = models.PositiveIntegerField(default=0, verbose_name=u'奖励数量')
    score = models.PositiveIntegerField(default=0, verbose_name=u'奖励分数')
    no = models.IntegerField(default=1, verbose_name=u'Number')
    class Meta:
        db_table = "t_project_role_allocation"
        verbose_name_plural = verbose_name = u"项目角色分配"

    def __unicode__(self):
        return u""


def get_project_doc_upload_to(instance, filename):
    return u'project/{}/{}'.format(instance.project_id, filename)


# 项目素材
class ProjectDoc(models.Model):
    project_id = models.IntegerField(verbose_name=u'项目')
    name = models.CharField(max_length=64, verbose_name=u'素材名称')
    type = models.CharField(max_length=32, verbose_name=u'素材类型')
    usage = models.PositiveIntegerField(default=3, choices=const.DOC_USAGE, verbose_name=u'用途')
    content = models.TextField(blank=True, null=True, verbose_name=u'内容')
    file = models.FileField(upload_to=get_project_doc_upload_to, storage=FileStorage(),
                            blank=True, null=True, verbose_name=u'文件')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    is_initial = models.BooleanField(default=False, verbose_name=u'初始素材')
    is_flow = models.BooleanField(default=False, verbose_name=u'流程素材')

    class Meta:
        db_table = "t_project_doc"
        verbose_name_plural = verbose_name = u"项目素材"

    def __unicode__(self):
        return u""


# 项目环节素材角色分配
class ProjectDocRole(models.Model):
    project_id = models.IntegerField(verbose_name=u'项目')
    node_id = models.IntegerField(verbose_name=u'环节')
    doc_id = models.IntegerField(verbose_name=u'素材')
    role_id = models.IntegerField(verbose_name=u'角色')
    no = models.IntegerField(default=1, verbose_name=u'Number')

    class Meta:
        db_table = "t_project_doc_role"
        verbose_name_plural = verbose_name = u"项目环节素材角色分配"

    def __unicode__(self):
        return u""


# 项目环节素材角色分配 todo 未使用
class ProjectDocRoleNew(models.Model):
    project_id = models.IntegerField(verbose_name=u'项目')
    node_id = models.IntegerField(verbose_name=u'环节')
    role_id = models.IntegerField(verbose_name=u'角色')
    docs = models.CharField(max_length=2048, blank=True, null=True, verbose_name=u'文档id')

    class Meta:
        db_table = "t_project_doc_role_new"
        verbose_name_plural = verbose_name = u"项目环节素材角色分配"

    def __unicode__(self):
        return u""


# 项目环节素材角色分配
class ProjectJump(models.Model):
    project_id = models.IntegerField(verbose_name=u'项目')
    node_id = models.IntegerField(verbose_name=u'环节')
    jump_project_id = models.IntegerField(verbose_name=u'跳转项目')

    class Meta:
        db_table = "t_project_jump"
        verbose_name_plural = verbose_name = u"项目环节跳转分配"

    def __unicode__(self):
        return u""

