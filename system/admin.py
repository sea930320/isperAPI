#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from utils import const
from models import *


# 参数配置
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'name', 'remark', 'create_time', 'update_time', 'del_flag']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段

    # def has_delete_permission(self, request, obj=None): # 去掉删除
    # def has_add_permission(self, request, obj=None): # 去掉增加
    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键
    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键
    # def delete_model(self, request, obj): # 删除单条
    # def delete_models(self, request, queryset): # 删除多条
    # def save_model(self, request, obj, form, change): # 保存
    # def save_related(self, request, form, formsets, change): # 保存关联表
    # def get_search_results(self, request, queryset, search_term): # 列表过滤
    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段
    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数
    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改


admin.site.register(Parameter, ParameterAdmin)


# APP版本发布
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'version', 'type', 'remark', 'total', 'create_time', 'update_time']
    fields = ['name', 'app', 'url', 'version', 'type', 'remark']

    # 去掉增加
    # def has_add_permission(self, request, obj=None):
    #     return False

    # 保存
    def save_model(self, request, obj, form, change):
        app = request.FILES.get('app', None)
        if app:
            obj.app = app
            obj.save()
            obj.url = '%s%s' % (const.WEB_HOST, obj.app.url)
        obj.save()

admin.site.register(AppRelease, AppReleaseAdmin)


# 用户日志
class UserLogsAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'username', 'method', 'param', 'result', 'remark', 'url', 'ip', 'create_time', 'del_flag']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段

    # def has_delete_permission(self, request, obj=None): # 去掉删除
    # def has_add_permission(self, request, obj=None): # 去掉增加
    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键
    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键
    # def delete_model(self, request, obj): # 删除单条
    # def delete_models(self, request, queryset): # 删除多条
    # def save_model(self, request, obj, form, change): # 保存
    # def save_related(self, request, form, formsets, change): # 保存关联表
    # def get_search_results(self, request, queryset, search_term): # 列表过滤
    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段
    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数
    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改


admin.site.register(UserLogs, UserLogsAdmin)


# 序号
class SequenceAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'update_time']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段

    # def has_delete_permission(self, request, obj=None): # 去掉删除
    # def has_add_permission(self, request, obj=None): # 去掉增加
    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键
    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键
    # def delete_model(self, request, obj): # 删除单条
    # def delete_models(self, request, queryset): # 删除多条
    # def save_model(self, request, obj, form, change): # 保存
    # def save_related(self, request, form, formsets, change): # 保存关联表
    # def get_search_results(self, request, queryset, search_term): # 列表过滤
    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段
    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数
    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改


# admin.site.register(Sequence, SequenceAdmin)


# 功能模块菜单
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['parent_id', 'name', 'code', 'style', 'url', 'target', 'visible', 'sort', 'create_time', 'update_time', 'del_flag']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段

    # def has_delete_permission(self, request, obj=None): # 去掉删除
    # def has_add_permission(self, request, obj=None): # 去掉增加
    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键
    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键
    # def delete_model(self, request, obj): # 删除单条
    # def delete_models(self, request, queryset): # 删除多条
    # def save_model(self, request, obj, form, change): # 保存
    # def save_related(self, request, form, formsets, change): # 保存关联表
    # def get_search_results(self, request, queryset, search_term): # 列表过滤
    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段
    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数
    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改


# admin.site.register(Module, ModuleAdmin)


# 文件
class UploadFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'file', 'md5sum', 'create_time', 'del_flag']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段

    # def has_delete_permission(self, request, obj=None): # 去掉删除
    # def has_add_permission(self, request, obj=None): # 去掉增加
    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键
    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键
    # def delete_model(self, request, obj): # 删除单条
    # def delete_models(self, request, queryset): # 删除多条
    # def save_model(self, request, obj, form, change): # 保存
    # def save_related(self, request, form, formsets, change): # 保存关联表
    # def get_search_results(self, request, queryset, search_term): # 列表过滤
    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段
    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数
    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改


admin.site.register(UploadFile, UploadFileAdmin)


