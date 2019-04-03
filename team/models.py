#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils import const


# 小组
class Team(models.Model):
    name = models.CharField(max_length=48, verbose_name=u'名称')
    leader = models.IntegerField(verbose_name=u'组长')
    open_join = models.PositiveIntegerField(default=1, choices=const.TEAM_OPEN_JOIN, verbose_name=u'开放邀请')
    created_by = models.IntegerField(verbose_name=u'创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_team"
        verbose_name_plural = verbose_name = u"小组"

    def __unicode__(self):
        return u""


# 小组成员
class TeamMember(models.Model):
    team_id = models.IntegerField(verbose_name=u'小组')
    user_id = models.IntegerField(verbose_name=u'用户')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_team_member"
        verbose_name_plural = u"小组成员"
        verbose_name = u"小组成员"

    def __unicode__(self):
        return u""
