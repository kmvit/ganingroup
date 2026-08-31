# -*- coding: utf-8 -*-
"""Завести документы сайта (сертификаты, декларации) и убрать старые заглушки.

Файлы кладутся в media/docs/ отдельно (scp на бой). Здесь только записи в БД.
Идемпотентно: get_or_create по имени файла.
"""
from django.db import migrations

from content.docs_seed import DOCS, OBSOLETE_TITLES


def seed(apps, schema_editor):
    Document = apps.get_model('content', 'Document')
    Document.objects.filter(title__in=OBSOLETE_TITLES).delete()
    for i, (filename, title, kind, summary) in enumerate(DOCS, 1):
        Document.objects.get_or_create(
            file=f'docs/{filename}',
            defaults=dict(title=title, kind=kind, summary=summary, order=i * 10))


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_seed_object_cases'),
    ]

    operations = [migrations.RunPython(seed, noop)]
