#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from project.models import Project
from account.models import Tuser

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
    node_id = models.IntegerField(blank=True, null=True, verbose_name=u'当前环节')
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