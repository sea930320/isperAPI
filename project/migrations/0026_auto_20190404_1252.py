# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-04 12:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0025_auto_20170918_1815'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_share',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5171\u4eab'),
        ),
        migrations.AddField(
            model_name='project',
            name='protected',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u4fdd\u62a4'),
        ),
        migrations.AlterField(
            model_name='projectdocrolenew',
            name='docs',
            field=models.CharField(blank=True, max_length=2048, null=True, verbose_name='\u6587\u6863id'),
        ),
    ]
