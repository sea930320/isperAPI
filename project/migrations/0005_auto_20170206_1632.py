# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-06 16:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0004_auto_20170206_1440'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectdoc',
            name='create_time',
        ),
        migrations.RemoveField(
            model_name='projectdoc',
            name='del_flag',
        ),
        migrations.RemoveField(
            model_name='projectdoc',
            name='update_time',
        ),
        migrations.AlterField(
            model_name='projectdoc',
            name='is_initial',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u4e3a\u521d\u59cb\u7d20\u6750'),
        ),
        migrations.AlterField(
            model_name='projectrole',
            name='max',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u6700\u5927\u4eba\u6570'),
        ),
        migrations.AlterField(
            model_name='projectrole',
            name='min',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u6700\u5c0f\u4eba\u6570'),
        ),
        migrations.AlterField(
            model_name='projectroleallocation',
            name='num',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u5956\u52b1\u6570\u91cf'),
        ),
        migrations.AlterField(
            model_name='projectroleallocation',
            name='score',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u5956\u52b1\u5206\u6570'),
        ),
    ]
