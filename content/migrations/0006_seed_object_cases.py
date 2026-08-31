# -*- coding: utf-8 -*-
"""Наполнить страницы кейсов существующих объектов (текст был в вёрстке).

Данными, а не пересевом: на бою объекты уже заведены с фото. Заполняем только
пустые поля кейса, чтобы не затирать ручные правки заказчика.
"""
from django.db import migrations

from content.cases import case_for
from content.utils import slugify_ru


def fill(apps, schema_editor):
    ProjectObject = apps.get_model('content', 'ProjectObject')
    ObjectStat = apps.get_model('content', 'ObjectStat')
    # осиротевшая страница-заглушка кейса: теперь кейсы берутся из объектов
    Page = apps.get_model('core', 'Page')
    Page.objects.filter(slug='obekt').delete()
    for obj in ProjectObject.objects.all():
        # нормализуем слаг в латиницу (были кириллические)
        latin = slugify_ru(obj.title)[:200]
        if latin and not obj.slug.isascii():
            obj.slug = latin
            obj.save(update_fields=['slug'])
        data = case_for(obj.title)
        if not data or obj.context or obj.headline:
            continue
        for field, val in data.items():
            if field != 'stats':
                setattr(obj, field, val)
        obj.save()
        if not obj.stats.exists():
            for i, (value, sup, label, note) in enumerate(data.get('stats', []), 1):
                ObjectStat.objects.create(project=obj, value=value, sup=sup,
                                          label=label, note=note, order=i * 10)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_projectobject_challenge_projectobject_context_and_more'),
        ('core', '0005_sitesettings_map_api_key'),
    ]

    operations = [migrations.RunPython(fill, noop)]
