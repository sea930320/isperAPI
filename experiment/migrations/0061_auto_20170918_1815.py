# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-09-18 18:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0060_auto_20170918_0910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experimentdoccontent',
            name='created_by',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u521b\u5efa\u8005'),
        ),
    ]
