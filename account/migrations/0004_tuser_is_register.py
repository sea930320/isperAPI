# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-27 10:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_auto_20170208_1452'),
    ]

    operations = [
        migrations.AddField(
            model_name='tuser',
            name='is_register',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u5df2\u5728\u73af\u4fe1\u6ce8\u518c'),
        ),
    ]
