# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-24 11:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0026_auto_20190404_1252'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='is_share',
            new_name='is_group_share',
        ),
        migrations.AddField(
            model_name='project',
            name='is_company_share',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u96c6\u7fa4\u5171\u4eab'),
        ),
    ]
