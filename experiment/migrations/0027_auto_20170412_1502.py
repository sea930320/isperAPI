# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-12 15:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0026_auto_20170412_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experimenttranspath',
            name='step',
            field=models.IntegerField(blank=True, default=1, null=True, verbose_name='\u6b65\u9aa4'),
        ),
    ]
