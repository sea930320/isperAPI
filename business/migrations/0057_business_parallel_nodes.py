# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-08-13 05:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0056_businessparallelnodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='parallel_nodes',
            field=models.ManyToManyField(to='business.BusinessParallelNodes'),
        ),
    ]
