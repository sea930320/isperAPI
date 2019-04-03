# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-13 14:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0003_auto_20170210_1527'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentSpeak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experiment_id', models.IntegerField(verbose_name='\u5b9e\u9a8cid')),
                ('node_id', models.IntegerField(verbose_name='\u73af\u8282id')),
                ('user_id', models.IntegerField(verbose_name='\u7533\u8bf7\u4eba')),
                ('times', models.IntegerField(verbose_name='\u53d1\u8a00\u6b21\u6570')),
                ('status', models.PositiveIntegerField(verbose_name='\u72b6\u6001')),
            ],
            options={
                'db_table': 't_experiment_speak',
                'verbose_name': '\u7533\u8bf7\u53d1\u8a00',
                'verbose_name_plural': '\u7533\u8bf7\u53d1\u8a00',
            },
        ),
        migrations.AlterModelOptions(
            name='experimentrolestatus',
            options={'verbose_name': '\u5b9e\u9a8c\u73af\u8282\u89d2\u8272\u72b6\u6001', 'verbose_name_plural': '\u5b9e\u9a8c\u73af\u8282\u89d2\u8272\u72b6\u6001'},
        ),
        migrations.RenameField(
            model_name='experimentrolestatus',
            old_name='status',
            new_name='come_status',
        ),
        migrations.AddField(
            model_name='experiment',
            name='control_status',
            field=models.PositiveIntegerField(default=1, verbose_name='\u8868\u8fbe\u7ba1\u7406\u72b6\u6001'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='experiment',
            name='node_id',
            field=models.IntegerField(default=1, verbose_name='\u5f53\u524d\u73af\u8282'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='experimentrolestatus',
            name='sitting_status',
            field=models.PositiveIntegerField(default=1, verbose_name='\u5165\u5e2d\u9000\u5e2d\u72b6\u6001'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='experimentrolestatus',
            name='stand_status',
            field=models.PositiveIntegerField(default=1, verbose_name='\u8d77\u7acb\u5750\u4e0b\u72b6\u6001'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='experiment',
            name='course_class_id',
            field=models.IntegerField(verbose_name='\u8bfe\u5802id'),
        ),
    ]
