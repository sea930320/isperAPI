# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-20 15:42
from __future__ import unicode_literals

from django.db import migrations, models
import utils.storage


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0002_auto_20170120_1504'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roleimagefile',
            name='avatar',
        ),
        migrations.RemoveField(
            model_name='roleimagefile',
            name='gender',
        ),
        migrations.AddField(
            model_name='roleimage',
            name='avatar',
            field=models.ImageField(blank=True, null=True, storage=utils.storage.ImageStorage(), upload_to=b'images/', verbose_name='\u5f62\u8c61'),
        ),
        migrations.AddField(
            model_name='roleimage',
            name='gender',
            field=models.PositiveSmallIntegerField(choices=[(1, '\u7537'), (2, '\u5973')], default=1, verbose_name='\u6027\u522b'),
        ),
    ]
