# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-09 22:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0015_merge_20190609_2032'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessReportStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_id', models.IntegerField(verbose_name='\u5360\u4f4d')),
                ('schedule_status', models.PositiveIntegerField(choices=[(0, '\u521d\u59cb'), (1, '\u5b89\u6392'), (2, '\u4e0a\u4f4d')], default=1, verbose_name='\u5b89\u6392\u72b6\u6001')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business', verbose_name='Business')),
                ('business_role_allocation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessRoleAllocation', verbose_name='Business Role Allocation')),
                ('path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessTransPath', verbose_name='\u5b9e\u9a8c\u8def\u5f84')),
            ],
            options={
                'db_table': 't_business_report_status',
                'verbose_name': '\u5b9e\u9a8c\u4efb\u52a1\u573a\u666f\u62a5\u544a\u72b6\u6001',
                'verbose_name_plural': '\u5b9e\u9a8c\u4efb\u52a1\u573a\u666f\u62a5\u544a\u72b6\u6001',
            },
        ),
    ]
