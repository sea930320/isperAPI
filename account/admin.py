#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin, messages
from models import *
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import ReadOnlyPasswordHashField
import json


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=u'密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label=u'确认密码', widget=forms.PasswordInput)

    class Meta:
        model = Tuser
        fields = ('username', 'nickname', 'gender', 'name', 'email', 'phone', 'qq', 'identity', 'tclass', 'is_active')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if len(password1) < 6:
            raise forms.ValidationError(u"密码长度不能少于6位")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(u"密码不一致")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.save()
        logger.info('user.pk:%s-is_register:%s' % (user.pk, user.is_register))
        # 在环信注册用户
        try:
            easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
            logger.info(u'easemob register_new_user:{},{},{}'.format(user.pk, easemob_success, easemob_result))
            if easemob_success:
                user.is_register = True
        except Exception as e:
            logger.exception(u'register_new_user exception:{}'.format(str(e)))
        user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            "<a href=\"../password/\">this form</a>."
        ),
    )

    class Meta:
        model = Tuser
        fields = ('username', 'password', 'nickname', 'gender', 'name', 'email', 'phone', 'qq', 'identity', 'tclass',
                  'is_active', 'is_admin')

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            if len(password) < 6:
                raise forms.ValidationError(u"密码长度不能少于6位")
        return self.initial["password"]


def delete_selected(modeladmin, request, queryset):
    for user in queryset:
        if user.is_superuser:
            continue
        # 删除权限
        user.groups.clear()
        user.group = None
        # 逻辑删除
        user.del_flag = const.DELETE_FLAG_YES
        user.is_active = False

        try:
            easemob_success, easemob_result = easemob.delete_user(user.pk)
            if easemob_success:
                user.is_register = False
            else:
                result = json.loads(easemob_result)
                if result['error'] == 'service_resource_not_found':
                    user.is_register = False
            logger.info('easemob delete_the_account:%s,%s,%s' % (user.pk, easemob_success, easemob_result))
        except Exception as e:
            logger.exception("delete_the_account exception：%s", str(e))
        user.save()
    messages.success(request, u"删除操作完成")

delete_selected.short_description = u'删除'


def disabled_selected(modeladmin, request, queryset):
    for user in queryset:
        if user.is_superuser:
            continue
        user.is_active = False

        try:
            easemob_success, easemob_result = easemob.delete_user(user.pk)
            if easemob_success:
                user.is_register = False
            else:
                result = json.loads(easemob_result)
                if result['error'] == 'service_resource_not_found':
                    user.is_register = False
            logger.info('easemob disabled_selected:%s,%s,%s' % (user.pk, easemob_success, easemob_result))
        except Exception as e:
            logger.exception("disabled_selected exception：%s", str(e))
        user.save()
    messages.success(request, u"禁用操作完成")

disabled_selected.short_description = u'禁用'


def active_selected(modeladmin, request, queryset):
    for user in queryset:
        if user.is_superuser and user.is_register:
            continue
        user.is_active = True
        user.del_flag = const.DELETE_FLAG_NO

        try:
            easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
            if easemob_success:
                user.is_register = True
            else:
                result = json.loads(easemob_result)
                if result['error'] == 'duplicate_unique_property_exists':
                    user.is_register = True
            logger.info(u'easemob active_selected:{},{},{}'.format(user.pk, easemob_success, easemob_result))
        except Exception as e:
            logger.exception(u'active_selected exception:{}'.format(str(e)))
        user.save()
    messages.success(request, u"激活操作完成")

active_selected.short_description = u'激活'


# 用户
class TuserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ['username', 'name', 'gender', 'email', 'phone', 'qq', 'identity', 'tclass',
                    'is_active', 'is_register', 'create_time', 'update_time', 'del_flag']
    list_filter = ['identity', 'is_active', 'is_register', 'del_flag', 'create_time']  # 过滤字段
    # list_editable = []  # 列表编辑字段
    # readonly_fields = []  # 只读字段
    search_fields = ('username', 'nickname',)
    ordering = ('-create_time',)
    actions = [disabled_selected, active_selected, delete_selected]
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('username', 'name', 'password')}),
        (u'用户信息', {'fields': ('nickname', 'gender', 'email', 'phone', 'qq', 'identity', 'tclass', 'tcompany',
                              'is_active')}),
        (u'用户权限', {'fields': ('director', 'manage', 'is_admin')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'name', 'password1', 'password2')}),
        (u'用户信息', {'fields': ('nickname', 'gender', 'email', 'phone', 'qq', 'identity', 'tclass', 'tcompany',
                              'is_active')}),
        (u'用户权限', {'fields': ('director', 'manage', 'is_admin')}),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(TuserAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if formfield and formfield.widget:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
        return formfield

    # 去掉删除
    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super(TuserAdmin, self).get_queryset(request)
        return qs
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


admin.site.register(Tuser, TuserAdmin)
admin.site.unregister(Group)


# 班级
class TClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'no', 'create_time', 'update_time']
    fields = ['name', 'year', 'no']
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


admin.site.register(TClass, TClassAdmin)


# 单位
class TCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'create_time', 'update_time']
    fields = ['name']


admin.site.register(TCompany, TCompanyAdmin)


