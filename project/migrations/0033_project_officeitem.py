# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-05-24 13:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0061_tcourse'),
        ('project', '0032_auto_20190524_0151'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='officeItem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.OfficeItems'),
        ),
    ]
