#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from account.models import Tuser


# 公告
class Notice(models.Model):
    author = models.ForeignKey(Tuser, verbose_name=u'作者')
    title = models.CharField(max_length=68, blank=True, null=True, verbose_name=u'标题')
    intro = models.CharField(max_length=256, verbose_name=u'概要')
    content = models.TextField(verbose_name=u'内容')
    hit = models.IntegerField(verbose_name=u'阅读数')
    top = models.IntegerField(verbose_name=u'置顶')
    status = models.PositiveIntegerField(verbose_name=u'状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_notice"
        verbose_name_plural = u"公告"
        verbose_name = u"公告"

    def __unicode__(self):
        return self.title


# 消息
class TMsg(models.Model):
    from_user = models.ForeignKey(Tuser, related_name='from_user_id', verbose_name=u'发件人')
    to_user = models.ForeignKey(Tuser, related_name='to_user_id', verbose_name=u'收件人')
    experiment_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验ID')
    content = models.CharField(max_length=255, verbose_name=u'内容')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    host = models.ForeignKey('self', blank=True, null=True, verbose_name=u'主题贴')
    read_status = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否阅读')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_msg"
        ordering = ('-create_time',)
        verbose_name_plural = u"消息"
        verbose_name = u"消息"

    def __unicode__(self):
        return u''


class TBusinessMsg(models.Model):
    from_user = models.ForeignKey(Tuser, related_name='from_user_id_business', verbose_name=u'发件人')
    to_user = models.ForeignKey(Tuser, related_name='to_user_id_business', verbose_name=u'收件人')
    business_id = models.IntegerField(blank=True, null=True, verbose_name=u'实验ID')
    content = models.CharField(max_length=255, verbose_name=u'内容')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    host = models.ForeignKey('self', blank=True, null=True, verbose_name=u'主题贴')
    read_status = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否阅读')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_msg_bussiness"
        ordering = ('-create_time',)
        verbose_name_plural = u"消息"
        verbose_name = u"消息"

    def __unicode__(self):
        return u''
