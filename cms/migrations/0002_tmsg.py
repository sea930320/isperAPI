# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-04 12:52
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TMsg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experiment_id', models.IntegerField(blank=True, null=True, verbose_name='\u5b9e\u9a8cID')),
                ('content', models.CharField(max_length=255, verbose_name='\u5185\u5bb9')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('read_status', models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u9605\u8bfb')),
                ('del_flag', models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5220\u9664')),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_user_id', to=settings.AUTH_USER_MODEL, verbose_name='\u53d1\u4ef6\u4eba')),
                ('host', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cms.TMsg', verbose_name='\u4e3b\u9898\u8d34')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_user_id', to=settings.AUTH_USER_MODEL, verbose_name='\u6536\u4ef6\u4eba')),
            ],
            options={
                'ordering': ('-create_time',),
                'db_table': 't_msg',
                'verbose_name': '\u6d88\u606f',
                'verbose_name_plural': '\u6d88\u606f',
            },
        ),
    ]
