# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-09 15:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0041_experimentdoccontent_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentPositionStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experiment_id', models.IntegerField(verbose_name='\u5b9e\u9a8c')),
                ('node_id', models.IntegerField(verbose_name='\u73af\u8282')),
                ('path_id', models.IntegerField(blank=True, null=True, verbose_name='\u5b9e\u9a8c\u8def\u5f84')),
                ('position_id', models.IntegerField(verbose_name='\u5360\u4f4d')),
                ('sitting_status', models.PositiveIntegerField(choices=[(1, '\u5f85\u5165\u5e2d'), (2, '\u5f85\u9000\u5e2d')], default=1, verbose_name='\u5165\u5e2d\u9000\u5e2d\u72b6\u6001')),
            ],
            options={
                'db_table': 't_experiment_position_status',
                'verbose_name': '\u5b9e\u9a8c\u4efb\u52a1\u573a\u666f\u5360\u4f4d\u72b6\u6001',
                'verbose_name_plural': '\u5b9e\u9a8c\u4efb\u52a1\u573a\u666f\u5360\u4f4d\u72b6\u6001',
            },
        ),
    ]
