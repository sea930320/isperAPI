# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-30 22:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_auto_20190427_0358'),
    ]

    operations = [
        migrations.AddField(
            model_name='tcompanytype',
            name='content',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tcompanytype',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='tcompanytype',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
