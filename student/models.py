#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from utils.storage import *
from utils import const
from project.models import Project, ProjectDoc
from account.models import Tuser, TJobType, OfficeItems, TCompany, TParts
from project.models import ProjectRoleAllocation
from workflow.models import FlowNode, SelectDecideItem
from business.models import *


# 课堂
class StudentWatchingTeam(models.Model):
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE)
    name = models.CharField(max_length=48, verbose_name=u'Team Name')
    type = models.IntegerField(default=0, verbose_name=u'Team Type')  # 0=>public, 1=>ask access
    team_leader = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Team Leader', related_name="student_team_leader_set")
    members = models.ManyToManyField(Tuser, verbose_name=u'Team Members')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_student_watching_team"
        verbose_name_plural = verbose_name = u"StudentWatchingTeams"

    def __unicode__(self):
        return str(self.name)


class StudentWatchingBusiness(models.Model):
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE, verbose_name=u'University')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Watching Business')
    team = models.ForeignKey(StudentWatchingTeam, on_delete=models.CASCADE, verbose_name=u'Watching Team')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Created By')

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_student_watching_business"
        verbose_name_plural = verbose_name = u"StudentWatchingBusinesses"

    def __unicode__(self):
        return str(self.university_id)
