# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-08 21:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0043_auto_20190508_2101'),
        ('group', '0021_auto_20190508_2120'),
    ]

    operations = [
        migrations.AddField(
            model_name='tgroupmanagerassistants',
            name='actions',
            field=models.ManyToManyField(to='account.TAction'),
        ),
    ]
