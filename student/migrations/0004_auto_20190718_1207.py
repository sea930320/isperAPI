# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-18 04:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_studentwatchingteam_team_leader'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentwatchingteam',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='studentwatchingteam',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
