# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-04-30 22:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0034_auto_20190430_2246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='officeitems',
            name='kinds',
        ),
        migrations.AddField(
            model_name='officeitems',
            name='kinds',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='account.OfficeKinds'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='tcourseitems',
            name='kinds',
        ),
        migrations.AddField(
            model_name='tcourseitems',
            name='kinds',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='account.TCourseKinds'),
            preserve_default=False,
        ),
    ]
