# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-17 14:58
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=68, null=True, verbose_name='\u6807\u9898')),
                ('intro', models.CharField(max_length=256, verbose_name='\u6982\u8981')),
                ('content', models.TextField(verbose_name='\u5185\u5bb9')),
                ('hit', models.IntegerField(verbose_name='\u9605\u8bfb\u6570')),
                ('top', models.IntegerField(verbose_name='\u7f6e\u9876')),
                ('status', models.PositiveIntegerField(verbose_name='\u72b6\u6001')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('del_flag', models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5220\u9664')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u4f5c\u8005')),
            ],
            options={
                'db_table': 't_notice',
                'verbose_name': '\u516c\u544a',
                'verbose_name_plural': '\u516c\u544a',
            },
        ),
    ]