#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from suit.admin import SortableModelAdmin
from models import *


# 流程
class FlowAdmin(admin.ModelAdmin):
    list_display = ['name', 'animation1', 'animation2', 'type_label', 'task_label', 'copy_from', 'xml',
                    'created_by', 'status', 'create_time', 'update_time', 'del_flag']
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


# admin.site.register(Flow, FlowAdmin)


# 程序模块
class FlowProcessAdmin(SortableModelAdmin):
    list_display = ['name', 'type', 'can_switch', 'file', 'image', 'create_time', 'update_time']
    fields = ['name', 'type', 'can_switch', 'file', 'image', 'preview']
    list_filter = ['type']  # 过滤字段
    sortable = 'sort'
    # list_editable = []  # 列表编辑字段
    readonly_fields = ('preview',)

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

    def preview(self, obj):
        if obj.image:
            return u'''<a href="%s"  target="_blank">
                <img src="%s" style="height:200px;width:200px;"></img></a>''' % (obj.image.url,
                                                                                 obj.image.url)
        else:
            return u'暂无'

    preview.short_description = u'场景截图预览'
    preview.allow_tags = True

admin.site.register(FlowProcess, FlowProcessAdmin)


# 功能动作
class FlowActionAdmin(SortableModelAdmin):
    list_display = ['name', 'cmd', 'order']
    fields = ['name', 'cmd']
    # list_filter = []  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段
    sortable = 'order'

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


admin.site.register(FlowAction, FlowActionAdmin)


# 场景动作
class ProcessActionAdmin(SortableModelAdmin):
    list_display = ['name', 'cmd', 'process', 'order']
    fields = ['name', 'cmd', 'process']
    list_filter = ['process']
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段
    sortable = 'order'

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
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'process':
            kwargs["queryset"] = FlowProcess.objects.filter(type=1)
        return super(ProcessActionAdmin, self).formfield_for_foreignkey(db_field, request=None, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(ProcessActionAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if formfield and formfield.widget:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
        return formfield

admin.site.register(ProcessAction, ProcessActionAdmin)


# 场景站位
class FlowPositionAdmin(admin.ModelAdmin):
    list_display = ['process', 'position', 'code_position', 'actor1', 'actor2', 'type', 'create_time', 'update_time']
    fields = ['process', 'position', 'code_position', 'actor1', 'actor2', 'type']
    list_filter = ['process']  # 过滤字段
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
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'process':
            kwargs["queryset"] = FlowProcess.objects.filter(type=1)
        return super(FlowPositionAdmin, self).formfield_for_foreignkey(db_field, request=None, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(FlowPositionAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if formfield and formfield.widget:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
        return formfield

admin.site.register(FlowPosition, FlowPositionAdmin)


class RoleImageTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(RoleImageType, RoleImageTypeAdmin)


class RoleImageFileInline(admin.TabularInline):
    model = RoleImageFile
    extra = 0


class RoleImageAdmin(admin.ModelAdmin):
    list_display = ['type', 'name', 'gender']
    inlines = (RoleImageFileInline, )
    list_filter = ['type', 'gender']
    readonly_fields = ['preview']  # 只读字段

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(RoleImageAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if formfield and formfield.widget:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
        return formfield

    def get_formsets(self, request, obj=None):
        for inline in self.get_inline_instances(request):
            formset = inline.get_formset(request, obj)
            if obj:
                formset.extra = 0
            yield formset

    def preview(self, obj):
        if obj.avatar:
            return u'''<a href="%s"  target="_blank">
                <img src="%s" style="height:200px;width:200px;"></img></a>''' % (obj.avatar.url,
                                                                                 obj.avatar.url)
        else:
            return u'暂无'

    preview.short_description = u'形象预览'
    preview.allow_tags = True

admin.site.register(RoleImage, RoleImageAdmin)
