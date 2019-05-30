#!/usr/bin/python
# -*- coding=utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db import models
from utils.storage import *
from utils import const


# 实验任务
class Experiment(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'名称')
    huanxin_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'环信id')
    project_id = models.IntegerField(verbose_name=u'项目')
    show_nickname = models.BooleanField(default=False, verbose_name=u'昵称显示组员')
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')
    team_id = models.IntegerField(verbose_name=u'小组')
    status = models.PositiveIntegerField(default=1, choices=const.EXPERIMENT_STATUS, verbose_name=u'状态')
    created_by = models.IntegerField(verbose_name=u'创建者')
    course_class_id = models.IntegerField(blank=True, null=True, verbose_name=u'课堂id')
    node_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前环节')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前路径')
    cur_project_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前项目')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    finish_time = models.DateTimeField(blank=True, null=True, verbose_name=u'实际完成时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_experiment"
        ordering = ('-create_time', )
        verbose_name_plural = verbose_name = u"实验任务"

    def __unicode__(self):
        return self.name


# 小组成员角色分配
class MemberRole(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    project_id = models.IntegerField(blank=True, null=True, verbose_name=u'项目')
    team_id = models.IntegerField(verbose_name=u'小组')
    role_id = models.IntegerField(verbose_name=u'角色')
    user_id = models.PositiveIntegerField(verbose_name=u'用户')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_member_role"
        verbose_name_plural = verbose_name = u"小组成员角色分配"

    def __unicode__(self):
        return u""


# 实验流转路径
class ExperimentTransPath(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    project_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前项目')
    node_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前环节')
    task_id = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'xml中task id')
    step = models.IntegerField(default=1, blank=True, null=True, verbose_name=u'步骤')
    control_status = models.PositiveIntegerField(default=1, choices=const.EXPERIMENT_CONTROL_STATUS,
                                                 verbose_name=u'表达管理状态')
    vote_status = models.PositiveIntegerField(choices=const.EXPERIMENT_VOTE_STATUS, default=1, verbose_name=u'投票状态')

    class Meta:
        db_table = "t_experiment_trans_path"
        ordering = ['step']
        verbose_name_plural = verbose_name = u"实验流转路径"

    def __unicode__(self):
        return self.experiment_id


def get_experiment_doc_upload_to(instance, filename):
    return u'experiment/{}/{}'.format(instance.experiment_id, filename)


# 实验提交文件
class ExperimentDoc(models.Model):
    filename = models.CharField(max_length=64, verbose_name=u'名称')
    file = models.FileField(upload_to=get_experiment_doc_upload_to, storage=FileStorage(), verbose_name=u'文件')
    content = models.TextField(blank=True, null=True, verbose_name=u'内容')
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    created_by = models.IntegerField(verbose_name=u'创建者')
    node_id = models.IntegerField(verbose_name=u'环节')
    role_id = models.IntegerField(blank=True, null=True, verbose_name=u'角色')
    sign = models.CharField(max_length=12, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.BooleanField(default=False, verbose_name=u'签名状态')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_experiment_doc"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"实验提交文件"

    def __unicode__(self):
        return self.filename


# 实验心得
class ExperimentExperience(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    created_by = models.IntegerField(verbose_name=u'创建者')
    content = models.TextField(verbose_name=u'心得')
    status = models.PositiveSmallIntegerField(choices=const.SUBMIT_STATUS, default=1, verbose_name=u'提交状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_experiment_experience"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"实验心得"

    def __unicode__(self):
        return u""


# 消息
class ExperimentMessage(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    user_id = models.IntegerField(verbose_name=u'用户id')
    role_id = models.IntegerField(verbose_name=u'角色')
    node_id = models.IntegerField(verbose_name=u'环节')
    file_id = models.IntegerField(blank=True, null=True, verbose_name=u'文件')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    user_name = models.CharField(max_length=8, blank=True, null=True, verbose_name=u'姓名')
    role_name = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'角色名称')
    msg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'消息内容')
    msg_type = models.CharField(max_length=10, verbose_name=u'消息类型')
    ext = models.TextField(verbose_name=u'自定义拓展属性')
    opt_status = models.BooleanField(default=False, verbose_name=u'操作状态')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=u'消息发送时间')

    class Meta:
        db_table = "t_experiment_message"
        verbose_name_plural = verbose_name = u"消息"

    def __unicode__(self):
        return u""


# 消息文件
class ExperimentMessageFile(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节')
    user_id = models.IntegerField(verbose_name=u'用户id')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    file = models.FileField(upload_to=get_experiment_doc_upload_to, storage=FileStorage(), verbose_name=u'文件')
    length = models.PositiveIntegerField(blank=True, null=True, verbose_name=u'语音时长', help_text=u'单位为秒，这个属性只有语音消息有')
    url = models.CharField(max_length=100, blank=True, null=True, verbose_name=u'图片语音等文件的网络URL',
                           help_text=u'图片和语音消息有这个属性')
    filename = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'文件名称', help_text=u'图片和语音消息有这个属性')
    secret = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'获取文件的secret',
                              help_text=u'图片和语音消息有这个属性')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 't_experiment_message_file'
        verbose_name_plural = verbose_name = u'消息文件'

    def __unicode__(self):
        return self.file.name


# 实验环节角色状态
class ExperimentRoleStatus(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节')
    user_id = models.IntegerField(blank=True, null=True, verbose_name=u'用户')
    role_id = models.IntegerField(verbose_name=u'角色')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    speak_times = models.IntegerField(default=0, verbose_name=u'发言次数')
    submit_status = models.PositiveIntegerField(choices=const.SUBMIT_STATUS, default=9, verbose_name=u'提交状态')
    show_status = models.PositiveIntegerField(choices=const.SHOW_STATUS, default=9, verbose_name=u'展示状态')
    come_status = models.PositiveIntegerField(choices=const.COME_STATUS, default=9, verbose_name=u'带入带出状态')
    sitting_status = models.PositiveIntegerField(choices=const.SITTING_STATUS, default=1, verbose_name=u'入席退席状态')
    stand_status = models.PositiveIntegerField(choices=const.STAND_STATUS, default=2, verbose_name=u'起立坐下状态')
    vote_status = models.PositiveIntegerField(choices=const.VOTE_STATUS, default=0, verbose_name=u'投票状态')

    class Meta:
        db_table = "t_experiment_role_status"
        verbose_name_plural = verbose_name = u"实验环节角色状态"

    def __unicode__(self):
        return u""


# 实验环节占位状态
class ExperimentPositionStatus(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节')
    path_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验路径')
    position_id = models.IntegerField(verbose_name=u'占位')
    role_id = models.IntegerField(blank=True, null=True, verbose_name=u'角色')
    sitting_status = models.PositiveIntegerField(choices=const.SITTING_STATUS, default=1, verbose_name=u'入席退席状态')

    class Meta:
        db_table = "t_experiment_position_status"
        verbose_name_plural = verbose_name = u"实验任务场景占位状态"

    def __unicode__(self):
        return u""


# 实验环节笔记
class ExperimentNotes(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节')
    created_by = models.IntegerField(verbose_name=u'创建')
    content = models.TextField(verbose_name=u'内容')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_experiment_notes"
        verbose_name_plural = verbose_name = u"实验环节笔记"

    def __unicode__(self):
        return u""


# 用户编辑模版内容
class ExperimentDocContent(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节id')
    doc_id = models.IntegerField(blank=True, null=True, verbose_name=u'模版id')
    name = models.CharField(max_length=64, verbose_name=u'模板名称')
    content = models.TextField(verbose_name=u'内容')
    file = models.FileField(upload_to=get_experiment_doc_upload_to, storage=FileStorage(),
                            blank=True, null=True, verbose_name=u'文件')
    sign = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.PositiveIntegerField(choices=const.SIGN_STATUS, default=0, verbose_name=u'签名状态')
    file_type = models.PositiveSmallIntegerField(choices=const.FILE_TYPE, default=0, verbose_name=u'文件类型')
    role_id = models.IntegerField(blank=True, null=True, verbose_name=u'角色')
    has_edited = models.BooleanField(default=False, verbose_name=u'是否已编辑')
    created_by = models.IntegerField(blank=True, null=True, verbose_name=u'创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_experiment_doc_content"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"用户编辑模版内容"

    def __unicode__(self):
        return self.name


# 实验环节报告席占位状态
class ExperimentReportStatus(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节')
    path_id = models.IntegerField(verbose_name=u'实验路径')
    role_id = models.IntegerField(verbose_name=u'角色')
    position_id = models.IntegerField(verbose_name=u'占位')
    schedule_status = models.PositiveIntegerField(choices=const.SCHEDULE_STATUS, default=1, verbose_name=u'安排状态')

    class Meta:
        db_table = "t_experiment_report_status"
        verbose_name_plural = verbose_name = u"实验任务场景报告状态"

    def __unicode__(self):
        return u""


# 实验环节文档签字记录
class ExperimentDocSign(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节id')
    doc_id = models.IntegerField(verbose_name=u'上传文档id')
    role_id = models.IntegerField(verbose_name=u'角色')
    sign = models.CharField(max_length=18, blank=True, null=True, verbose_name=u'签名')
    sign_status = models.PositiveIntegerField(choices=const.SIGN_STATUS, default=0, verbose_name=u'签名状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = "t_experiment_doc_sign"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"实验环节文档签字记录"

    def __unicode__(self):
        return u""


# 快速评价样本分类
class EvaluateType(models.Model):
    label = models.CharField(max_length=32, verbose_name=u"分类")

    class Meta:
        db_table = "t_evaluate_type"
        verbose_name_plural = verbose_name = u"评价分类"

    def __unicode__(self):
        return self.label


# 快速评价样本
class EvaluatePool(models.Model):
    evaluate_type = models.ForeignKey(EvaluateType, verbose_name=u"分类")
    evaluate_level = models.CharField(max_length=32, choices=((u"A", u"A"), (u"B", u"B"), (u"C", u"C"), (u"D", u"D")),
                                      verbose_name=u'等级')
    evaluate_content = models.CharField(max_length=255, verbose_name=u"评语样本")

    class Meta:
        db_table = "t_evaluate_pool"
        ordering = ['evaluate_type', 'evaluate_level']
        verbose_name_plural = verbose_name = u"评价样本"

    def __unicode__(self):
        return u""


# 总体评价
class EvaluateExperiment(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    user_id = models.IntegerField(verbose_name=u'用户id')
    content = models.CharField(max_length=255, verbose_name=u"内容")
    sys_score = models.CharField(max_length=32, verbose_name=u"系统评分")
    teacher_score = models.CharField(max_length=32, verbose_name=u"教师评分")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    create_by_id = models.IntegerField(verbose_name=u'提交人')

    class Meta:
        db_table = "t_evaluate_experiment"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"总体评价"

    def __unicode__(self):
        return u""


# 环节评价
class EvaluateNode(models.Model):
    experiment_id = models.IntegerField(db_index=True, verbose_name=u'实验id')
    node_id = models.IntegerField(db_index=True, verbose_name=u'环节id')
    user_id = models.IntegerField(verbose_name=u'用户id')
    content = models.CharField(max_length=255, verbose_name=u"内容")
    sys_score = models.CharField(max_length=32, verbose_name=u"系统评分")  # 这个字段不要了，统一在t_evaluate_experiment
    teacher_score = models.CharField(max_length=32, verbose_name=u"教师评分")  # 这个字段不要了，统一在t_evaluate_experiment
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    create_by_id = models.IntegerField(verbose_name=u'提交人')

    class Meta:
        db_table = "t_evaluate_node"
        ordering = ['-create_time']
        verbose_name_plural = verbose_name = u"环节评价"

    def __unicode__(self):
        return u""

