# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-10 16:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0003_auto_20170210_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='created_by',
            field=models.IntegerField(default=1, verbose_name='\u521b\u5efa\u8005'),
            preserve_default=False,
        ),
    ]
