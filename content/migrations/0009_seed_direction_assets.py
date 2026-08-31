# -*- coding: utf-8 -*-
"""Активы на «О группе» — из направлений (галочка + их фото).

Проставляем флаг и подписи существующим направлениям по ASSET_MAP и удаляем
старые плитки-активы (Card, section='assets') на «О группе», чтобы не дублировать.
Только для пустых полей — ручные правки не затираем.
"""
from django.db import migrations

from content.assets_seed import ASSET_MAP


def fill(apps, schema_editor):
    Direction = apps.get_model('content', 'Direction')
    for d in Direction.objects.all():
        data = ASSET_MAP.get(d.title)
        if not data or d.show_in_assets:
            continue
        d.show_in_assets = True
        if not d.asset_title:
            d.asset_title = data[0]
        if not d.asset_text:
            d.asset_text = data[1]
        d.save(update_fields=['show_in_assets', 'asset_title', 'asset_text'])

    # старые плитки активов на «О группе» больше не нужны
    Card = apps.get_model('core', 'Card')
    Card.objects.filter(page__slug='o_gruppe', section='assets').delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_direction_asset_text_direction_asset_title_and_more'),
        ('core', '0006_sitesettings_delivery_radius_km_and_more'),
    ]

    operations = [migrations.RunPython(fill, noop)]
