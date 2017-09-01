# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-30 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0018_auto_20170829_2345'),
    ]

    operations = [
        migrations.AddField(
            model_name='mesa',
            name='electores',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='opcion',
            name='codigo_dne',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='partido',
            name='color',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='partido',
            name='referencia',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='lugarvotacion',
            name='electores',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]