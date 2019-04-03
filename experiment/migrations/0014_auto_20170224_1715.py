# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-24 17:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0013_auto_20170223_1642'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experiment',
            options={'ordering': ('-create_time',), 'verbose_name': '\u5b9e\u9a8c\u4efb\u52a1', 'verbose_name_plural': '\u5b9e\u9a8c\u4efb\u52a1'},
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='addr',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='chat_type',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='filename',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='from_id',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='lat',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='length',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='lng',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='msg_id',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='secret',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='to_id',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='type',
        ),
        migrations.RemoveField(
            model_name='experimentmessage',
            name='url',
        ),
        migrations.AddField(
            model_name='experimentmessage',
            name='file_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u6587\u4ef6'),
        ),
        migrations.AddField(
            model_name='experimentmessage',
            name='user_id',
            field=models.IntegerField(default=1, verbose_name='\u7528\u6237id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='experimentmessagefile',
            name='filename',
            field=models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=64, null=True, verbose_name='\u6587\u4ef6\u540d\u79f0'),
        ),
        migrations.AddField(
            model_name='experimentmessagefile',
            name='length',
            field=models.PositiveIntegerField(blank=True, help_text='\u5355\u4f4d\u4e3a\u79d2\uff0c\u8fd9\u4e2a\u5c5e\u6027\u53ea\u6709\u8bed\u97f3\u6d88\u606f\u6709', null=True, verbose_name='\u8bed\u97f3\u65f6\u957f'),
        ),
        migrations.AddField(
            model_name='experimentmessagefile',
            name='secret',
            field=models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=64, null=True, verbose_name='\u83b7\u53d6\u6587\u4ef6\u7684secret'),
        ),
        migrations.AddField(
            model_name='experimentmessagefile',
            name='url',
            field=models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=100, null=True, verbose_name='\u56fe\u7247\u8bed\u97f3\u7b49\u6587\u4ef6\u7684\u7f51\u7edcURL'),
        ),
        migrations.AddField(
            model_name='experimentmessagefile',
            name='user_id',
            field=models.IntegerField(default=1, verbose_name='\u7528\u6237id'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='experimentmessage',
            name='experiment_id',
            field=models.IntegerField(db_index=True, verbose_name='\u5b9e\u9a8cid'),
        ),
        migrations.AlterField(
            model_name='experimentmessage',
            name='ext',
            field=models.CharField(max_length=512, verbose_name='\u81ea\u5b9a\u4e49\u62d3\u5c55\u5c5e\u6027'),
        ),
        migrations.AlterField(
            model_name='experimentmessage',
            name='msg',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='\u6d88\u606f\u5185\u5bb9'),
        ),
        migrations.AlterField(
            model_name='experimentmessage',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u6d88\u606f\u53d1\u9001\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='experimentmessagefile',
            name='experiment_id',
            field=models.IntegerField(db_index=True, verbose_name='\u5b9e\u9a8cid'),
        ),
    ]
