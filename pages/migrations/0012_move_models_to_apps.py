# -*- coding: utf-8 -*-
"""Модели переезжают из pages в core / content / calc / leads.

Переезд только на уровне состояния Django: физические таблицы (pages_*)
остаются теми же — новые модели привязаны к ним через db_table.
В базе не выполняется ни одной операции, поэтому данные не затрагиваются.
"""
from django.db import migrations

MOVED = [
    'Card', 'MenuItem', 'Page', 'SiteSettings',                       # -> core
    'Stat', 'Direction', 'ProjectObject', 'Department', 'TeamMember',
    'Review', 'Vacancy', 'Document', 'TimelineEvent', 'MapPoint',     # -> content
    'ConcreteGrade', 'DeliveryZone',                                  # -> calc
    'Lead', 'HaulerLead', 'VacancyApplication',                       # -> leads
]


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0011_fix_price_note'),
        ('core', '0001_initial'),
        ('content', '0001_initial'),
        ('calc', '0001_initial'),
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.DeleteModel(name=name) for name in MOVED],
            database_operations=[],
        ),
    ]
