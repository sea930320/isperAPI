# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-31 12:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0018_auto_20170321_1821'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experimentmessage',
            name='ext',
            field=models.TextField(verbose_name='\u81ea\u5b9a\u4e49\u62d3\u5c55\u5c5e\u6027'),
        ),
    ]
