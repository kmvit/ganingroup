# -*- coding: utf-8 -*-
"""Проставить координаты существующим точкам карты (для Яндекс.Карты).

Данными, а не через seed_content --reset: на бою уже есть загруженный заказчиком
контент (фото и т.п.), полный пересев его бы стёр. Координаты ставим только там,
где их ещё нет, чтобы не затирать ручные правки.
"""
from django.db import migrations

# старый заголовок → (широта, долгота, своя площадка, новый заголовок или None)
COORDS = {
    'завод · КМВ':        (44.061033, 42.986830, True, 'завод · Пятигорск'),
    'завод · Пятигорск':  (44.061033, 42.986830, True, None),
    'карьер · Зольская':  (44.050000, 43.280000, True, None),
    'Ставрополь':         (45.044500, 41.969000, False, None),
    'Невинномысск':       (44.630000, 41.945000, False, None),
    'Нальчик':            (43.480600, 43.607000, False, None),
    'Черкесск':           (44.226900, 42.046600, False, None),
}


def set_coords(apps, schema_editor):
    MapPoint = apps.get_model('content', 'MapPoint')
    for mp in MapPoint.objects.all():
        data = COORDS.get(mp.title)
        if not data or mp.lat is not None:
            continue
        lat, lng, is_own, new_title = data
        mp.lat, mp.lng, mp.is_own = lat, lng, is_own
        if new_title:
            mp.title = new_title
        mp.save(update_fields=['lat', 'lng', 'is_own', 'title'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_mappoint_lat_mappoint_lng_alter_mappoint_is_own_and_more'),
    ]

    operations = [
        migrations.RunPython(set_coords, noop),
    ]
