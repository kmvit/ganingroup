# -*- coding: utf-8 -*-
"""Убирает из общей оговорки фразу про доставку.

Раньше текст всегда сообщал «Цены указаны без доставки», даже когда клиент
выбрал доставку и она уже посчитана в итоге. Теперь эта фраза подставляется
автоматически, поэтому из сохранённого текста её нужно убрать —
но только если заказчик не переписал текст сам.
"""
from django.db import migrations

OLD = ('Цены указаны без доставки. Окончательная стоимость зависит от объёма, '
       'графика поставок и удалённости объекта.')
NEW = 'Окончательная стоимость зависит от объёма, графика поставок и удалённости объекта.'


def fix(apps, schema_editor):
    SiteSettings = apps.get_model('pages', 'SiteSettings')
    for s in SiteSettings.objects.all():
        if (s.price_note or '').strip() == OLD:
            s.price_note = NEW
            s.save(update_fields=['price_note'])


def unfix(apps, schema_editor):
    SiteSettings = apps.get_model('pages', 'SiteSettings')
    for s in SiteSettings.objects.all():
        if (s.price_note or '').strip() == NEW:
            s.price_note = OLD
            s.save(update_fields=['price_note'])


class Migration(migrations.Migration):

    dependencies = [('pages', '0010_alter_sitesettings_price_note')]

    operations = [migrations.RunPython(fix, unfix)]
