# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-20 12:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sbicodes', '0002_sbicodehierarchy_qa_tree'),
    ]

    base_query = 'DROP TABLE IF EXISTS {table} CASCADE;'

    operations = [
        migrations.RunSQL(base_query.format(table='hr_cbs_sbi_endcode')),
        migrations.RunSQL(base_query.format(table='hr_cbs_sbi_hoofdcat')),
        migrations.RunSQL(base_query.format(table='hr_cbs_sbi_rootnode')),
        migrations.RunSQL(base_query.format(table='hr_cbs_sbi_section')),
        migrations.RunSQL(base_query.format(table='hr_cbs_sbi_subcat')),
        migrations.RunSQL(base_query.format(table='hr_cbs_sbicode')),
    ]
