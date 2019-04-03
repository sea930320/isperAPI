# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-10 14:14
from __future__ import unicode_literals

from django.db import migrations, models
import utils.storage
import workflow.models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0024_auto_20170221_1933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='flowaction',
            options={'verbose_name': '\u529f\u80fd\u52a8\u4f5c', 'verbose_name_plural': '\u529f\u80fd\u52a8\u4f5c'},
        ),
        migrations.AddField(
            model_name='flowaction',
            name='order',
            field=models.IntegerField(default=1, verbose_name='\u6392\u5e8f'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='processaction',
            name='order',
            field=models.IntegerField(default=1, verbose_name='\u6392\u5e8f'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='flow',
            name='diagram',
            field=models.ImageField(blank=True, null=True, storage=utils.storage.ImageStorage(), upload_to=b'workflow/diagram/', verbose_name='\u6d41\u7a0b\u56fe'),
        ),
        migrations.AlterField(
            model_name='flowdocs',
            name='file',
            field=models.FileField(blank=True, null=True, storage=utils.storage.FileStorage(), upload_to=workflow.models.get_flow_doc_upload_to, verbose_name='\u6587\u4ef6'),
        ),
        migrations.AlterField(
            model_name='flowprocess',
            name='file',
            field=models.FileField(blank=True, null=True, storage=utils.storage.ImageStorage(), upload_to=b'workflow/process/', verbose_name='\u573a\u666f\u6587\u4ef6'),
        ),
        migrations.AlterField(
            model_name='flowprocess',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=utils.storage.ImageStorage(), upload_to=b'workflow/process/', verbose_name='\u573a\u666f\u622a\u56fe'),
        ),
        migrations.AlterField(
            model_name='roleimage',
            name='avatar',
            field=models.ImageField(blank=True, null=True, storage=utils.storage.ImageStorage(), upload_to=b'avatar/', verbose_name='\u5f62\u8c61'),
        ),
        migrations.AlterField(
            model_name='roleimagefile',
            name='file',
            field=models.FileField(blank=True, null=True, storage=utils.storage.FileStorage(), upload_to=b'avatar/', verbose_name='\u5f62\u8c61\u6587\u4ef6'),
        ),
    ]
