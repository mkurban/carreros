# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-19 02:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='localidad',
            name='departamento',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='geo.Departamento'),
            preserve_default=False,
        ),
    ]