# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-07-08 16:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0065_auto_20190623_1900'),
        ('business', '0041_merge_20190708_2107'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField(verbose_name='Business Answer')),
            ],
            options={
                'db_table': 't_business_answer',
                'verbose_name': 't_business_answers',
                'verbose_name_plural': 't_business_answers',
            },
        ),
        migrations.CreateModel(
            name='BusinessQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(choices=[(0, 'Choose Question'), (1, 'Blank Fill Question'), (2, 'Normal Question')], default=0, verbose_name='Question Type')),
                ('select_option', models.IntegerField(blank=True, null=True, verbose_name='Question Type')),
                ('title', models.TextField(verbose_name='Question Title')),
                ('description', models.TextField(verbose_name='Question Description')),
            ],
            options={
                'db_table': 't_business_question',
                'verbose_name': 't_business_questions',
                'verbose_name_plural': 't_business_questions',
            },
        ),
        migrations.CreateModel(
            name='BusinessQuestionCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case', models.TextField(verbose_name='Question Case Option')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessQuestion', verbose_name='Business Question')),
            ],
            options={
                'db_table': 't_business_question_case',
                'verbose_name': 't_business_question_cases',
                'verbose_name_plural': 't_business_question_cases',
            },
        ),
        migrations.CreateModel(
            name='BusinessSurvey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.IntegerField(null=True, verbose_name='\u5f53\u524d\u9879\u76ee')),
                ('title', models.TextField(verbose_name='Survey Title')),
                ('description', models.TextField(verbose_name='Survey Description')),
                ('step', models.IntegerField(default=0, verbose_name='Survey Step')),
                ('start_time', models.DateTimeField(blank=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4')),
                ('end_quote', models.TextField(verbose_name='Survey End Quotion')),
                ('target', models.IntegerField(choices=[(0, 'All'), (1, 'Business'), (2, 'Node')], default=0, verbose_name='Survey Target')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business', verbose_name='Business')),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow.FlowNode', verbose_name='Node ID')),
            ],
            options={
                'db_table': 't_business_survey',
                'verbose_name': 't_business_surveys',
                'verbose_name_plural': 't_business_surveys',
            },
        ),
        migrations.AddField(
            model_name='businessquestion',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessSurvey', verbose_name='Business Survey'),
        ),
        migrations.AddField(
            model_name='businessanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessQuestion', verbose_name='Business Question'),
        ),
        migrations.AddField(
            model_name='businessanswer',
            name='question_cases',
            field=models.ManyToManyField(to='business.BusinessQuestionCase', verbose_name='Qustion Case Answer'),
        ),
        migrations.AddField(
            model_name='businessanswer',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.BusinessSurvey', verbose_name='Business Survey'),
        ),
    ]
