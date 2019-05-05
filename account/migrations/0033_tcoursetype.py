# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-30 22:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0032_tjobtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='TCourseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('content', models.CharField(max_length=256)),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 't_courseType',
            },
        ),
    ]
