# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 15:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_auto_20170206_1632'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectdoc',
            name='is_initial',
        ),
        migrations.AlterField(
            model_name='projectdoc',
            name='usage',
            field=models.PositiveIntegerField(default=1, verbose_name='\u7528\u9014'),
        ),
    ]
