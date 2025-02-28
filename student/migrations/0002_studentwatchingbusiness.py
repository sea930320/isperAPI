# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-17 13:32
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0047_merge_20190717_1903'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0065_tuser_last_business_id'),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentWatchingBusiness',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.IntegerField(choices=[(1, '\u662f'), (0, '\u5426')], default=0, verbose_name='\u662f\u5426\u5220\u9664')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business', verbose_name='Watching Business')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.StudentWatchingTeam', verbose_name='Watching Team')),
                ('university', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.TCompany', verbose_name='University')),
            ],
            options={
                'db_table': 't_student_watching_business',
                'verbose_name': 'StudentWatchingBusinesses',
                'verbose_name_plural': 'StudentWatchingBusinesses',
            },
        ),
    ]
