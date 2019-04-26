#!/usr/bin/python
# -*- coding=utf-8 -*-
import logging

from time import sleep
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from utils import const
from utils import easemob

logger = logging.getLogger(__name__)


# 班级
class TClass(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'名称')
    year = models.IntegerField(blank=True, null=True, verbose_name=u'年')
    no = models.IntegerField(blank=True, null=True, verbose_name=u'班号')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_class"
        verbose_name_plural = u"班级"
        verbose_name = u"班级"

    def __unicode__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **kwargs):
        if (not username) or (not password):
            raise ValueError("UserManager create user param error")

        user = self.model(username=username)
        user.set_password(password)
        if kwargs:
            if kwargs.get("nickname", None):
                user.nickname = kwargs["nickname"]
            if kwargs.get("email", None):
                user.email = kwargs["email"]
            if kwargs.get("phone", None):
                user.phone = kwargs["phone"]
        user.save(using=self._db)
        # 在环信注册用户
        try:
            easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
            logger.info(u'easemob register_new_user:{},{},{}'.format(user.pk, easemob_success, easemob_result))
            sleep(0.2)
        except Exception as e:
            logger.exception(u'register_new_user exception:{}'.format(str(e)))
        return user

    def create_superuser(self, username, password):
        accounts = self.create_user(username=username, password=password)
        accounts.is_superuser = True
        accounts.is_admin = True
        accounts.save(using=self._db)
        return accounts


# 角色
class TRole(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'名称')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = "t_role"
        verbose_name_plural = u"角色"
        verbose_name = u"角色"

    def __unicode__(self):
        return self.name


class OfficeKinds(models.Model):
    name = models.CharField(max_length=256)

    class Meta:
        db_table = "t_officeKinds"

    def __unicode__(self):
        return self.name


class OfficeItems(models.Model):
    name = models.CharField(max_length=256)
    kinds = models.ManyToManyField(OfficeKinds)

    class Meta:
        db_table = "t_officeItems"

    def __unicode__(self):
        return self.name


class TCompanyType(models.Model):
    name = models.CharField(max_length=256)

    class Meta:
        db_table = "t_companyType"

    def __unicode__(self):
        return self.name


# 单位
class TCompany(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'名称')
    comment = models.CharField(max_length=256)
    created_by = models.ForeignKey('Tuser', related_name="created_company_set")
    companyType = models.ForeignKey('TCompanyType')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    group = models.ForeignKey('group.AllGroups', on_delete=models.CASCADE)

    class Meta:
        db_table = "t_company"
        verbose_name_plural = u"单位"
        verbose_name = u"单位"

    def __unicode__(self):
        return self.name


class TCompanyManagers(models.Model):
    tuser = models.ForeignKey('Tuser', on_delete=models.CASCADE)
    tcompany = models.ForeignKey(TCompany, on_delete=models.CASCADE)

    class Meta:
        db_table = "t_company_managers"
        verbose_name_plural = u"单位经理员"
        verbose_name = u"单位经理员"

    def __unicode__(self):
        return self.tuser.username + "--" + self.tcompany.name


# 用户
class Tuser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=18, db_index=True, unique=True, verbose_name=u'账号')
    nickname = models.CharField(max_length=24, blank=True, null=True, verbose_name=u'昵称')
    gender = models.PositiveIntegerField(choices=const.GENDER, default=1, verbose_name=u'性别')
    name = models.CharField(max_length=256, verbose_name=u'姓名')
    email = models.CharField(max_length=56, blank=True, null=True, verbose_name=u'邮箱')
    phone = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'联系方式')
    qq = models.CharField(max_length=28, blank=True, null=True, verbose_name=u'QQ')
    identity = models.PositiveIntegerField(default=1, choices=const.IDENTITY, verbose_name=u'身份')
    type = models.PositiveIntegerField(default=1, choices=const.USER_TYPE, verbose_name=u'类型')
    ip = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'ip')
    is_active = models.BooleanField(default=True, verbose_name=u'账号状态')
    is_admin = models.BooleanField(default=False, verbose_name=u'超级管理员')
    tclass = models.ForeignKey(TClass, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u'班级')
    tcompany = models.ForeignKey(TCompany, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u'所在单位')
    director = models.BooleanField(default=False, verbose_name=u'是否具有指导权限')
    manage = models.BooleanField(default=False, verbose_name=u'是否具有管理权限')
    assigned_by = models.IntegerField(blank=True, null=True, verbose_name=u'权限是被谁赋予的')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    is_register = models.BooleanField(default=False, verbose_name=u'环信状态')
    last_experiment_id = models.IntegerField(blank=True, null=True, verbose_name=u'最后做的一个实验id')
    is_share = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否共享')
    avatar = models.ImageField(upload_to='avatars', null=True)
    roles = models.ManyToManyField(TRole)
    instructorItems = models.ManyToManyField(OfficeItems)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "t_user"
        verbose_name_plural = verbose_name = u"用户"

    def __unicode__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    @property
    def is_staff(self):
        return self.is_admin


# 用户角色
class TUserRole(models.Model):
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE)
    role = models.ForeignKey(TRole, on_delete=models.CASCADE)

    class Meta:
        db_table = "t_user_role"
        verbose_name_plural = u"用户角色"
        verbose_name = u"用户角色"

    def __unicode__(self):
        return self.user.name + " : " + self.role.name


