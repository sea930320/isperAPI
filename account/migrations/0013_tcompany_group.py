# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-19 00:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0005_auto_20190418_2059'),
        ('account', '0012_auto_20190411_0236'),
    ]

    operations = [
        migrations.AddField(
            model_name='tcompany',
            name='group',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='group.AllGroups'),
            preserve_default=False,
        ),
    ]
