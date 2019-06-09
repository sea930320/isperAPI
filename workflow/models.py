#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from account.models import Tuser
from account.models import TJobType, TRole
from utils import const
from utils.storage import *


# 流程
class Flow(models.Model):
    name = models.CharField(max_length=48, verbose_name=u'名称')
    animation1 = models.IntegerField(blank=True, null=True, verbose_name=u'渲染动画1')
    animation2 = models.IntegerField(blank=True, null=True, verbose_name=u'渲染动画2')
    type_label = models.IntegerField(verbose_name=u'实验类型标签')
    task_label = models.CharField(max_length=64, verbose_name=u'实验任务标签')
    copy_from = models.IntegerField(blank=True, null=True, verbose_name=u'复制流程ID')
    xml = models.TextField(blank=True, null=True, verbose_name=u'流程图xml数据')
    created_by = models.IntegerField(verbose_name=u'创建者')
    created_role = models.ForeignKey(TRole, models.CASCADE, verbose_name=u'创建者_ROLE')
    step = models.IntegerField(default=const.FLOW_STEP_0, verbose_name=u'设置步骤')
    status = models.IntegerField(choices=const.FLOW_STATUS, default=1, verbose_name=u'状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    protected = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否保护')
    is_share = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否共享')
    is_public = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否公开')

    class Meta:
        db_table = "t_flow"
        ordering = ['-create_time']
        verbose_name_plural = u"流程"
        verbose_name = u"流程"

    def __unicode__(self):
        return self.name


# 工作流环节
class FlowNode(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    name = models.CharField(max_length=48, verbose_name=u'环节名称')
    condition = models.CharField(max_length=68, blank=True, null=True, verbose_name=u'干扰')
    process = models.ForeignKey('FlowProcess', blank=True, null=True, on_delete=models.PROTECT, verbose_name=u'程序模块')
    look_on = models.BooleanField(default=False, verbose_name=u'是否允许旁观')
    step = models.IntegerField(default=0, verbose_name=u'排序')
    task_id = models.CharField(max_length=16, verbose_name=u'xml中task id')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_node"
        verbose_name_plural = verbose_name = u"工作流环节"
        ordering = ['name']

    def __unicode__(self):
        return self.name


# 程序模块
class FlowProcess(models.Model):
    name = models.CharField(max_length=48, verbose_name=u'名称')
    type = models.PositiveIntegerField(verbose_name=u'类型', choices=const.PROCESS_TYPE)
    file = models.FileField(upload_to='process/', storage=FileStorage(), blank=True, null=True, verbose_name=u'场景文件')
    image = models.ImageField(upload_to='process/', storage=ImageStorage(), blank=True, null=True, verbose_name=u'场景截图')
    can_switch = models.BooleanField(default=True, verbose_name=u'是否能切换视角')
    sort = models.IntegerField(default=0, blank=True, null=True, verbose_name=u'展示排序')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_process"
        verbose_name_plural = verbose_name = u"程序模块"
        ordering = ['sort']

    def __unicode__(self):
        return self.name


def get_flow_doc_upload_to(instance, filename):
    return u'workflow/{}/{}'.format(instance.flow_id, filename)


# 素材文档
class FlowDocs(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    name = models.CharField(max_length=68, verbose_name=u'名称')
    type = models.CharField(max_length=32, verbose_name=u'素材类型')
    usage = models.PositiveIntegerField(default=0, choices=const.DOC_USAGE, verbose_name=u'用途')
    content = models.TextField(blank=True, null=True, verbose_name=u'内容')
    file = models.FileField(upload_to=get_flow_doc_upload_to, storage=FileStorage(), blank=True, null=True,
                            verbose_name=u'文件')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_docs"
        ordering = ['-create_time']
        verbose_name_plural = u"素材文档"
        verbose_name = u"素材文档"

    def __unicode__(self):
        return self.name


# 流程环节素材分配
class FlowNodeDocs(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    node_id = models.IntegerField(verbose_name=u'环节')
    doc_id = models.IntegerField(verbose_name=u'素材')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_node_docs"
        verbose_name_plural = verbose_name = u"流程环节素材分配"

    def __unicode__(self):
        return u""


# 环节角色
class FlowRole(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    image_id = models.IntegerField(verbose_name=u'角色形象', null=True, blank=True)
    name = models.CharField(max_length=32, verbose_name=u'角色名称')
    type = models.CharField(max_length=28, verbose_name=u'角色类型', null=True, blank=True)
    min = models.IntegerField(verbose_name=u'最小人数', null=True, blank=True)
    max = models.IntegerField(verbose_name=u'最大人数', null=True, blank=True)
    category = models.PositiveIntegerField(verbose_name=u'类别', choices=const.ROLE_CATEGORY, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    capacity = models.IntegerField(verbose_name=u'人数', default=1)
    job_type = models.ForeignKey(TJobType, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "t_flow_role"
        verbose_name_plural = u"环节角色"
        verbose_name = u"环节角色"

    def __unicode__(self):
        return self.name


# 环节角色分配
class FlowRoleAllocation(models.Model):
    flow = models.ForeignKey(Flow, verbose_name=u'流程')
    node = models.ForeignKey(FlowNode, verbose_name=u'环节')
    role = models.ForeignKey(FlowRole, verbose_name=u'角色')
    can_start = models.BooleanField(verbose_name=u'Can Start the business', default=False)
    can_terminate = models.BooleanField(verbose_name=u'结束环节权限')
    can_brought = models.BooleanField(verbose_name=u'是否被带入')
    can_take_in = models.BooleanField(verbose_name=u'This guy will be taken in this step ', default=False)
    no = models.IntegerField(default=1, verbose_name=u'Number')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_role_allocation"
        verbose_name_plural = u"环节角色分配"
        verbose_name = u"环节角色分配"

    def __unicode__(self):
        return u""


# 角色环节分配优化拆分2个表，环节角色关系表，角色环节配置表
# class FlowRoleNodeAllocation(models.Model):
#     flow = models.ForeignKey(Flow, verbose_name=u'流程')
#     role = models.ForeignKey(FlowRole, verbose_name=u'角色')
#     allocation = models.TextField(blank=True, null=True, verbose_name=u'配置')
#     del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
#
#     class Meta:
#         db_table = "t_flow_role_node_allocation"
#         verbose_name_plural = verbose_name = u"环节角色配置"
#
#     def __unicode__(self):
#         return u""
#
#
# class FlowNodeRolesRef(models.Model):
#     flow = models.ForeignKey(Flow, verbose_name=u'流程')
#     node = models.ForeignKey(FlowNode, verbose_name=u'环节')
#     roles = models.CharField(max_length=2048, blank=True, null=True, verbose_name=u'角色id集合')
#     del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
#
#     class Meta:
#         db_table = "t_flow_node_roles_ref"
#         verbose_name_plural = verbose_name = u"环节角色关系"
#
#     def __unicode__(self):
#         return u""


# 功能动作
class FlowAction(models.Model):
    name = models.CharField(max_length=24, verbose_name=u'动作')
    cmd = models.CharField(max_length=100, blank=True, null=True, verbose_name=u'命令')
    order = models.IntegerField(verbose_name=u'排序')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_action"
        ordering = ['order']
        verbose_name_plural = u"功能动作"
        verbose_name = u"功能动作"

    def __unicode__(self):
        return self.name


# 场景动作
class ProcessAction(models.Model):
    name = models.CharField(max_length=24, verbose_name=u'名称')
    cmd = models.CharField(max_length=100, blank=True, null=True, verbose_name=u'命令')
    order = models.IntegerField(verbose_name=u'排序')
    process = models.ForeignKey(FlowProcess, on_delete=models.PROTECT, verbose_name=u'场景')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_process_action"
        ordering = ['order']
        verbose_name_plural = verbose_name = u"场景动作"

    def __unicode__(self):
        return self.name


# 角色动作设置
class FlowRoleActionNew(models.Model):
    flow = models.ForeignKey(Flow, verbose_name=u'流程')
    node = models.ForeignKey(FlowNode, verbose_name=u'环节')
    role = models.ForeignKey(FlowRole, verbose_name=u'角色')
    actions = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'功能动作')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_role_action_new"
        verbose_name_plural = verbose_name = u"角色动作"

    def __unicode__(self):
        return u""

# 角色动作设置
class FlowRoleAllocationAction(models.Model):
    flow = models.ForeignKey(Flow, verbose_name=u'流程')
    node = models.ForeignKey(FlowNode, verbose_name=u'环节')
    role_allocation = models.ForeignKey(FlowRoleAllocation, verbose_name=u'角色')
    actions = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'功能动作')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_role_alloction_action"
        verbose_name_plural = verbose_name = u"角色动作"

    def __unicode__(self):
        return u""

# 角色场景动画设置
class ProcessRoleActionNew(models.Model):
    flow = models.ForeignKey(Flow, verbose_name=u'流程')
    node = models.ForeignKey(FlowNode, verbose_name=u'环节')
    role = models.ForeignKey(FlowRole, verbose_name=u'角色')
    actions = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'场景动画配置')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_process_role_action_new"
        verbose_name_plural = verbose_name = u"角色场景动画"

    def __unicode__(self):
        return u""


# 场景站位
class FlowPosition(models.Model):
    process = models.ForeignKey(FlowProcess, on_delete=models.PROTECT, verbose_name=u'场景')
    position = models.CharField(max_length=32, verbose_name=u'场景站位')
    code_position = models.CharField(max_length=32, verbose_name=u'flash站位')
    actor1 = models.IntegerField(choices=const.DIRECTION, default=const.DIRECTION_FRONT)
    actor2 = models.IntegerField(choices=const.DIRECTION, default=const.DIRECTION_BACK)
    type = models.PositiveIntegerField(choices=const.SEAT_TYPE, default=0, verbose_name=u'站位类型')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_position"
        verbose_name_plural = verbose_name = u"场景站位"

    def __unicode__(self):
        return u""


# 角色站位
class FlowRolePosition(models.Model):
    flow_id = models.IntegerField(verbose_name=u'流程')
    node_id = models.IntegerField(verbose_name=u'环节')
    role_id = models.IntegerField(verbose_name=u'角色')
    position_id = models.IntegerField(verbose_name=u'站位')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_role_position"
        verbose_name_plural = verbose_name = u"角色站位"

    def __unicode__(self):
        return u""


# 流程流转
class FlowTrans(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'名称')
    flow_id = models.IntegerField(verbose_name=u'流程')
    incoming = models.CharField(max_length=32, verbose_name=u'输入环节')
    outgoing = models.CharField(max_length=32, verbose_name=u'输出环节')
    conditions = models.CharField(max_length=20, verbose_name=u'条件')
    remark = models.CharField(max_length=256, verbose_name=u'备注')
    sequence_flow_id = models.CharField(max_length=32, verbose_name=u'xml中sequenceFlow')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_flow_trans"
        verbose_name_plural = u"流程流转"
        verbose_name = u"流程流转"

    def __unicode__(self):
        return self.name


class RoleImageType(models.Model):
    name = models.CharField(max_length=24, verbose_name=u'名称')

    class Meta:
        db_table = "t_role_image_type"
        verbose_name_plural = verbose_name = u"角色形象类型"

    def __unicode__(self):
        return self.name


class RoleImage(models.Model):
    type = models.ForeignKey(RoleImageType, on_delete=models.PROTECT, verbose_name=u'角色形象类型')
    name = models.CharField(max_length=24, verbose_name=u'角色形象名称')
    gender = models.PositiveSmallIntegerField(default=1, choices=const.GENDER, verbose_name=u'性别')
    avatar = models.ImageField(upload_to='avatar/', storage=ImageStorage(), blank=True, null=True, verbose_name=u'形象')

    class Meta:
        db_table = "t_role_image"
        verbose_name_plural = verbose_name = u"角色形象"

    def __unicode__(self):
        return self.name


class RoleImageFile(models.Model):
    image = models.ForeignKey(RoleImage, verbose_name=u'角色形象')
    direction = models.PositiveSmallIntegerField(default=1, choices=const.DIRECTION, verbose_name=u'方向')
    file = models.FileField(upload_to='avatar/', storage=FileStorage(), blank=True, null=True, verbose_name=u'形象文件')

    class Meta:
        db_table = "t_role_image_file"
        verbose_name_plural = verbose_name = u"角色形象文件"

    def __unicode__(self):
        return self.image.name
