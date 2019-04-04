# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-04 12:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0046_flowdocs_file_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='flow',
            name='is_share',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5171\u4eab'),
        ),
        migrations.AddField(
            model_name='flow',
            name='protected',
            field=models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u4fdd\u62a4'),
        ),
    ]
