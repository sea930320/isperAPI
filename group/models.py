# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from account.models import Tuser


# Create your models here.
class Groups(models.Model):
    name = models.CharField(max_length=48)
    comment = models.CharField(max_length=256)
    publish = models.IntegerField(default=1, choices=((1, u"是"), (0, u"否")))
    default = models.IntegerField(default=0)

    class Meta:
        db_table = "t_groups"

    def __unicode__(self):
        return self.name


class GroupManagers(models.Model):
    user = models.ForeignKey(Tuser, on_delete=models.CASCADE)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)

    class Meta:
        db_table = "t_groupManagers"

    def __unicode__(self):
        return self.user.name + " : " + self.group.name
