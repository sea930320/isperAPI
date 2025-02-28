# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-07 14:44
from __future__ import unicode_literals

import business.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflow', '0057_flow_created_role'),
        ('business', '0011_auto_20190606_1315'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_id', models.IntegerField(blank=True, null=True, verbose_name='\u6587\u4ef6')),
                ('user_name', models.CharField(blank=True, max_length=8, null=True, verbose_name='\u59d3\u540d')),
                ('role_name', models.CharField(blank=True, max_length=32, null=True, verbose_name='\u89d2\u8272\u540d\u79f0')),
                ('msg', models.CharField(blank=True, max_length=512, null=True, verbose_name='\u6d88\u606f\u5185\u5bb9')),
                ('msg_type', models.CharField(max_length=10, verbose_name='\u6d88\u606f\u7c7b\u578b')),
                ('ext', models.TextField(verbose_name='\u81ea\u5b9a\u4e49\u62d3\u5c55\u5c5e\u6027')),
                ('opt_status', models.BooleanField(default=False, verbose_name='\u64cd\u4f5c\u72b6\u6001')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='\u6d88\u606f\u53d1\u9001\u65f6\u95f4')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business', verbose_name='Business')),
                ('business_role_allocation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessRoleAllocation', verbose_name='Business Role Allocation')),
                ('path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessTransPath', verbose_name='\u5b9e\u9a8c\u8def\u5f84')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 't_business_message',
                'verbose_name': '\u6d88\u606f',
                'verbose_name_plural': '\u6d88\u606f',
            },
        ),
        migrations.CreateModel(
            name='BusinessMessageFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(storage=utils.storage.FileStorage(), upload_to=business.models.get_business_doc_upload_to, verbose_name='\u6587\u4ef6')),
                ('length', models.PositiveIntegerField(blank=True, help_text='\u5355\u4f4d\u4e3a\u79d2\uff0c\u8fd9\u4e2a\u5c5e\u6027\u53ea\u6709\u8bed\u97f3\u6d88\u606f\u6709', null=True, verbose_name='\u8bed\u97f3\u65f6\u957f')),
                ('url', models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=100, null=True, verbose_name='\u56fe\u7247\u8bed\u97f3\u7b49\u6587\u4ef6\u7684\u7f51\u7edcURL')),
                ('filename', models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=64, null=True, verbose_name='\u6587\u4ef6\u540d\u79f0')),
                ('secret', models.CharField(blank=True, help_text='\u56fe\u7247\u548c\u8bed\u97f3\u6d88\u606f\u6709\u8fd9\u4e2a\u5c5e\u6027', max_length=64, null=True, verbose_name='\u83b7\u53d6\u6587\u4ef6\u7684secret')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business', verbose_name='Business')),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow.FlowNode', verbose_name='\u73af\u8282')),
                ('path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessTransPath', verbose_name='\u5b9e\u9a8c\u8def\u5f84')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 't_business_message_file',
                'verbose_name': '\u6d88\u606f\u6587\u4ef6',
                'verbose_name_plural': '\u6d88\u606f\u6587\u4ef6',
            },
        ),
    ]
