# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-02 21:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0036_tuser_class_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='tuser',
            name='student_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tuser',
            name='class_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
