# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-17 00:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0060_flowroleposition_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowroleactionnew',
            name='no',
            field=models.IntegerField(default=1, verbose_name='Number'),
        ),
    ]
