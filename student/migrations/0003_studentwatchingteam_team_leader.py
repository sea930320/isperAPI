# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-18 02:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0002_studentwatchingbusiness'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentwatchingteam',
            name='team_leader',
            field=models.ForeignKey(default=1763, on_delete=django.db.models.deletion.CASCADE, related_name='student_team_leader_set', to=settings.AUTH_USER_MODEL, verbose_name='Team Leader'),
            preserve_default=False,
        ),
    ]
