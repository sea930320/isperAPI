# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-18 04:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0062_processroleactionnew_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flowroleposition',
            name='position_id',
            field=models.IntegerField(default=None, null=True, verbose_name='\u7ad9\u4f4d'),
        ),
    ]
