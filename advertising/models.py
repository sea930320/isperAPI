# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from account.models import Tuser



class Advertising(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'名称')
    path = models.CharField(max_length=255, verbose_name=u'文件路径')
    file_type = models.CharField(max_length=10, verbose_name=u'文件类型')
    created_by = models.ForeignKey(Tuser, models.CASCADE, verbose_name=u'创建者')
    public_time = models.DateTimeField(blank=True, null=True, verbose_name=u'时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = "t_advertising"
        ordering = ['-create_time', '-update_time']
        verbose_name_plural = verbose_name = u"公告"

    def __unicode__(self):
        return self.name