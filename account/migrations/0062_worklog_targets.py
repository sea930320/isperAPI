# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-19 11:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0061_auto_20190518_0159'),
    ]

    operations = [
        migrations.AddField(
            model_name='worklog',
            name='targets',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='targets'),
        ),
    ]
