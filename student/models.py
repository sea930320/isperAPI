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
from course.models import *


# 课堂
class StudentWatchingTeam(models.Model):
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE)
    name = models.CharField(max_length=48, verbose_name=u'Team Name')
    type = models.IntegerField(default=0, verbose_name=u'Team Type')  # 0=>public, 1=>ask access
    team_leader = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Team Leader',
                                    related_name="student_team_leader_set")
    members = models.ManyToManyField(Tuser, verbose_name=u'Team Members')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_student_watching_team"
        verbose_name_plural = verbose_name = u"StudentWatchingTeams"
        ordering = ['-create_time']

    def __unicode__(self):
        return str(self.name)


class StudentWatchingBusiness(models.Model):
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE, verbose_name=u'University')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name=u'Course', null=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Watching Business')
    team = models.ForeignKey(StudentWatchingTeam, on_delete=models.CASCADE, verbose_name=u'Watching Team')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Created By')
    teamEval = models.TextField(verbose_name=u'Team Evaluation', default='')

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_student_watching_business"
        verbose_name_plural = verbose_name = u"StudentWatchingBusinesses"
        ordering = ['-create_time']

    def __unicode__(self):
        return str(self.university_id)

class StudentWatchingBusinessTeamMemberEval(models.Model):
    stwb = models.ForeignKey(StudentWatchingBusiness, on_delete=models.CASCADE, verbose_name=u'Student Watching Business')
    member = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Team Member')
    eval = models.TextField(verbose_name=u'Team Member Evaluation', default='')

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_student_watching_business_team_member_eval"
        verbose_name_plural = verbose_name = u"StudentWatchingBusinessTeamMemberEvals"
        ordering = ['-create_time']

    def __unicode__(self):
        return str(self.id)

class StudentRequestAssistStatus(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Watching Business')
    university = models.ForeignKey(TCompany, on_delete=models.CASCADE, verbose_name=u'University')
    requestedFrom = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Requested From',
                                      related_name='requested_from')
    requestedTo = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Requested To',
                                    related_name='requestedTo')
    status = models.IntegerField(default=0, verbose_name=u'Requested Status')  # 0=>pending, 1=>accepted, 2=>rejected

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "t_student_request_assist_status"
        verbose_name_plural = verbose_name = u"StudentRequestAssistStatuses"
        ordering = ['-create_time']

    def __unicode__(self):
        return str(self.business.id)


class StudentChatLog(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    from_user = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'From User', related_name="sent_from")
    msg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'消息内容')
    msg_type = models.IntegerField(default=0, verbose_name=u'Message Type')  # 0=> class group chat,
    ext = models.TextField(verbose_name=u'Message Ext')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_student_chatlog"
        verbose_name_plural = verbose_name = u"StudentChatLogs"

    def __unicode__(self):
        return str(self.business.id)


class StudentTodoList(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name=u'Business')
    created_by = models.ForeignKey(Tuser, on_delete=models.CASCADE, verbose_name=u'Created By', related_name="todo_created_by")
    name = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'todo name')
    student = models.ForeignKey(Tuser, on_delete=models.CASCADE, blank=True, null=True, verbose_name=u'Student', related_name="student")

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True)
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')


    class Meta:
        db_table = "t_student_todo_list"
        verbose_name_plural = verbose_name = u"StudentTodos"

    def __unicode__(self):
        return str(self.name)