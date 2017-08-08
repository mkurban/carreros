# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-08 03:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fiscales', '0011_auto_20170807_2002'),
    ]

    operations = [
        migrations.AddField(
            model_name='asignacionfiscaldemesa',
            name='comida',
            field=models.CharField(choices=[('no asignada', 'no asignada'), ('asignada', 'asignada'), ('recibida', 'recibida')], default='no asignada', max_length=50),
        ),
        migrations.AddField(
            model_name='asignacionfiscalgeneral',
            name='comida',
            field=models.CharField(choices=[('no asignada', 'no asignada'), ('asignada', 'asignada'), ('recibida', 'recibida')], default='no asignada', max_length=50),
        ),
    ]
