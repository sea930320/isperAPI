# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-30 12:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0067_auto_20190719_0321'),
    ]

    operations = [
        migrations.AddField(
            model_name='tuser',
            name='course_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
