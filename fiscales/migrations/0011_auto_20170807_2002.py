# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-07 23:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fiscales', '0010_auto_20170807_0041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fiscal',
            name='organizacion',
            field=models.ForeignKey(blank=True, help_text='Opcional. Para mostrar contactos extra del usuario', null=True, on_delete=django.db.models.deletion.CASCADE, to='fiscales.Organizacion'),
        ),
    ]
