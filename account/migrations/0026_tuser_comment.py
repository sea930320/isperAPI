# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-26 20:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0025_tcompany_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='tuser',
            name='comment',
            field=models.CharField(default=b'', max_length=256),
        ),
    ]
