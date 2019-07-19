#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from account.models import Tuser, TCompany, TCompanyManagers


# 课堂
class Course(models.Model):
    courseId = models.CharField(max_length=16, verbose_name=u'courseId')
    courseName = models.CharField(max_length=48, verbose_name=u'courseName')
    courseSeqNum = models.IntegerField(verbose_name=u'courseSeqNum')
    courseSemester = models.CharField(max_length=48, verbose_name=u'courseSemester')
    teacher = models.ForeignKey(Tuser, models.CASCADE, verbose_name=u'teacher', related_name="teacher")
    courseCount = models.IntegerField(verbose_name=u'courseCount')
    experienceTime = models.CharField(max_length=48, verbose_name=u'experienceTime')
    studentCount = models.IntegerField(verbose_name=u'studentCount')
    tcompany = models.ForeignKey(TCompany, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Tuser, models.CASCADE, verbose_name=u'创建者', related_name="created_by")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    type = models.IntegerField(default=0, verbose_name=u'type')

    class Meta:
        db_table = "t_course"
        verbose_name_plural = verbose_name = u"课堂"

    def __unicode__(self):
        return self.courseName


# 课堂
class UniversityLinkedCompany(models.Model):
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE, related_name="university_set")
    linked_company = models.ForeignKey(TCompany, on_delete=models.CASCADE, related_name="linked_company_set")
    seted_company_manager = models.ForeignKey(TCompanyManagers, blank=True, null=True, on_delete=models.CASCADE, related_name="seted_company_manager")
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'创建者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    seted_time = models.DateTimeField(blank=True, null=True, verbose_name=u'seted_time')
    message = models.CharField(max_length=100, verbose_name=u'message')
    status = models.IntegerField(default=0, verbose_name=u'status') # 0: request, 1: agree, 2: disagree, 3: canceled

    class Meta:
        db_table = "t_university_linked_company"
        verbose_name_plural = verbose_name = u"UniversityLinkedCompany"

    def __unicode__(self):
        return str(self.university_id)
