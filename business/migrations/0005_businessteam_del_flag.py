# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-05 00:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0004_auto_20190604_2221'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessteam',
            name='del_flag',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5220\u9664'),
        ),
    ]
