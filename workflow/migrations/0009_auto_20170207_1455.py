# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 14:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0008_auto_20170207_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flowdocs',
            name='usage',
            field=models.PositiveIntegerField(default=1, verbose_name='\u7528\u9014'),
        ),
    ]
