# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0059_processroleallocationaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowroleposition',
            name='no',
            field=models.IntegerField(default=1, verbose_name='Number'),
        ),
    ]
