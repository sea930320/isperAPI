# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-04 05:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0034_auto_20190704_1305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pollmember',
            name='vote_status',
        ),
        migrations.AddField(
            model_name='pollmember',
            name='poll_status',
            field=models.IntegerField(default=0, verbose_name='Poll status'),
        ),
    ]
