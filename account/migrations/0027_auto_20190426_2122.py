# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-26 21:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0026_tuser_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tuserrole',
            name='role',
        ),
        migrations.RemoveField(
            model_name='tuserrole',
            name='user',
        ),
        migrations.DeleteModel(
            name='TUserRole',
        ),
    ]
