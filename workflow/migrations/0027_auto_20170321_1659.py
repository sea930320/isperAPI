# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-21 16:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0026_auto_20170316_1022'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowposition',
            name='actor1',
            field=models.IntegerField(choices=[(1, '\u6b63'), (2, '\u80cc'), (3, '\u4fa7')], default=1),
        ),
        migrations.AddField(
            model_name='flowposition',
            name='actor2',
            field=models.IntegerField(choices=[(1, '\u6b63'), (2, '\u80cc'), (3, '\u4fa7')], default=2),
        ),
    ]
