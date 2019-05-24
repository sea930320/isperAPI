# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-22 22:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0059_trole_actions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tuser',
            name='tclass',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.TClass', verbose_name='\u73ed\u7ea7'),
        ),
        migrations.AlterField(
            model_name='tuser',
            name='tcompany',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.TCompany', verbose_name='\u6240\u5728\u5355\u4f4d'),
        ),
    ]
