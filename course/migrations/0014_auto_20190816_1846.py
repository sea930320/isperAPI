# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-08-16 10:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0013_auto_20190816_1829'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ['-create_time'], 'verbose_name': '\u8bfe\u5802', 'verbose_name_plural': '\u8bfe\u5802'},
        ),
    ]
