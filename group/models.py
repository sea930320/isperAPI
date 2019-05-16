# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from account.models import Tuser
from account.models import TPermission
from account.models import TAction


class AllGroups(models.Model):
    name = models.CharField(max_length=48)
    comment = models.CharField(max_length=256)
    publish = models.IntegerField(default=1, choices=((1, u"是"), (0, u"否")))
    default = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    groupManagers = models.ManyToManyField(Tuser, related_name="allgroups_set")
    groupManagerAssistants = models.ManyToManyField(Tuser, through='TGroupManagerAssistants', related_name="allgroups_set_assistants")
    groupInstructors = models.ManyToManyField(Tuser, related_name="allgroups_set_instructors")
    groupInstructorAssistants = models.ManyToManyField(Tuser, related_name="allgroups_set_instructor_assistants")

    class Meta:
        db_table = "t_allGroups"

    def __unicode__(self):
        return self.name


class TGroupChange(models.Model):
    user = models.ForeignKey(Tuser)
    reason = models.CharField(max_length=256, default='')
    target = models.ForeignKey(AllGroups)
    sAgree = models.IntegerField(default=0)
    tAgree = models.IntegerField(default=0)

    class Meta:
        db_table = "t_group_change"

    def __unicode__(self):
        return self.reason


class TGroupManagerAssistants(models.Model):
    all_groups = models.ForeignKey(AllGroups, on_delete=models.CASCADE)
    tuser = models.ForeignKey(Tuser, on_delete=models.CASCADE)
    actions = models.ManyToManyField(TAction)

    class Meta:
        # auto_created = True
        db_table = "t_allGroups_groupManagerAssistants"

    def __unicode__(self):
        return self.all_groups.name + ':' + self.tuser.name

