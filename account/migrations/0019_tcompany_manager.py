# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-25 10:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_auto_20190423_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='tcompany',
            name='manager',
            field=models.ManyToManyField(related_name='companyManager_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
