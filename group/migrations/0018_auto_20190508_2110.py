# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-08 21:10
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0017_tgroupmanagerassistants'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allgroups',
            name='groupManagerAssistants',
        ),
        migrations.AddField(
            model_name='allgroups',
            name='groupManagerAssistants',
            field=models.ManyToManyField(related_name='allgroups_set_assistants', through='group.TGroupManagerAssistants', to=settings.AUTH_USER_MODEL),
        ),
    ]
