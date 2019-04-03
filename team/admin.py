#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from models import *


# 小组
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'open_join', 'create_time', 'update_time', 'del_flag']
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


admin.site.register(Team, TeamAdmin)


# 小组成员
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['team_id', 'user_id', 'create_time', 'update_time', 'del_flag']
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


admin.site.register(TeamMember, TeamMemberAdmin)


