# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-03 09:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0031_remove_dataselectie_bag_vbid'),
    ]

    operations = [
        migrations.AddField(
            model_name='persoon',
            name='duur',
            field=models.CharField(blank=True, max_length=21, null=True),
        ),
        migrations.AddField(
            model_name='persoon',
            name='status',
            field=models.CharField(blank=True, max_length=21, null=True),
        ),
    ]