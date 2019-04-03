#!/usr/bin/python
# -*- coding=utf-8 -*-
import hashlib

from django.db import models
from utils.storage import *
from utils.const import DEVICE


# 参数配置
class Parameter(models.Model):
    key = models.CharField(max_length=48, verbose_name=u'key')
    value = models.CharField(max_length=256, verbose_name=u'值')
    name = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'名称')
    remark = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'说明')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_parameter"
        verbose_name_plural = u"参数配置"
        verbose_name = u"参数配置"

    def __unicode__(self):
        return self.name


# APP版本发布
class AppRelease(models.Model):
    name = models.CharField(max_length=58, verbose_name=u'名称')
    app = models.FileField(upload_to='app/', storage=ImageStorage(), blank=True, null=True, verbose_name=u'APP应用')
    url = models.CharField(max_length=128, verbose_name=u'下载链接')
    version = models.IntegerField(verbose_name=u'版本号')
    type = models.PositiveIntegerField(default=1, choices=DEVICE.items(), verbose_name=u'类型')
    remark = models.CharField(max_length=256, verbose_name=u'说明')
    total = models.IntegerField(verbose_name=u'下载统计')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_app_release"
        verbose_name_plural = u"APP版本发布"
        verbose_name = u"APP版本发布"

    def __unicode__(self):
        return self.name


# 用户日志
class UserLogs(models.Model):
    user_id = models.IntegerField(verbose_name=u'用户编号')
    username = models.CharField(max_length=28, blank=True, null=True, verbose_name=u'用户账号')
    method = models.CharField(max_length=68, blank=True, null=True, verbose_name=u'调用方法')
    param = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'参数')
    result = models.CharField(max_length=518, blank=True, null=True, verbose_name=u'结果')
    remark = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'备注')
    url = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'url')
    ip = models.CharField(max_length=28, blank=True, null=True, verbose_name=u'ip')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_user_logs"
        verbose_name_plural = u"用户日志"
        verbose_name = u"用户日志"

    def __unicode__(self):
        return u""


# 序号
class Sequence(models.Model):
    key = models.CharField(max_length=32, verbose_name=u'key')
    value = models.IntegerField(verbose_name=u'值')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = "t_sequence"
        verbose_name_plural = u"序号"
        verbose_name = u"序号"

    def __unicode__(self):
        return self.key


# 功能模块菜单
class Module(models.Model):
    parent_id = models.IntegerField(blank=True, null=True, verbose_name=u'上级')
    name = models.CharField(max_length=48, verbose_name=u'名称')
    code = models.CharField(max_length=48, verbose_name=u'代码')
    style = models.CharField(max_length=24, blank=True, null=True, verbose_name=u'样式')
    url = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'链接')
    target = models.PositiveIntegerField(blank=True, null=True, verbose_name=u'目标')
    visible = models.PositiveIntegerField(verbose_name=u'显示状态')
    sort = models.IntegerField(verbose_name=u'展示排序')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_module"
        verbose_name_plural = u"功能模块菜单"
        verbose_name = u"功能模块菜单"

    def __unicode__(self):
        return self.name


# 文件
class UploadFile(models.Model):
    filename = models.CharField(max_length=128, verbose_name=u'文件名')
    file = models.FileField(upload_to='files/%Y/%m/%d', storage=FileStorage(), verbose_name=u'文件')
    md5sum = models.CharField(max_length=128, verbose_name=u'MD5哈希值')
    created_by = models.IntegerField(verbose_name=u'上传者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_upload_file"
        verbose_name_plural = u"文件"
        verbose_name = u"文件"

    def __unicode__(self):
        return self.filename
