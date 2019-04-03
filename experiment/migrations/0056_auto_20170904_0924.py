# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-09-04 09:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0055_experimentdocsign'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experimentpositionstatus',
            name='sitting_status',
            field=models.PositiveIntegerField(choices=[(1, '\u672a\u5165\u5e2d'), (2, '\u5df2\u5165\u5e2d')], default=1, verbose_name='\u5165\u5e2d\u9000\u5e2d\u72b6\u6001'),
        ),
        migrations.AlterField(
            model_name='experimentrolestatus',
            name='sitting_status',
            field=models.PositiveIntegerField(choices=[(1, '\u672a\u5165\u5e2d'), (2, '\u5df2\u5165\u5e2d')], default=1, verbose_name='\u5165\u5e2d\u9000\u5e2d\u72b6\u6001'),
        ),
    ]
