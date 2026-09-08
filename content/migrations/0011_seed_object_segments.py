# -*- coding: utf-8 -*-
"""Перенос привязки объектов к сегментам: направление → галочки «Сегменты».

До этого страницы решений отбирали объекты по полю «Направление»
(«Коммерческое» — вообще все). Правило переносим один раз, чтобы выдача
не изменилась, а дальше привязка задаётся галочками в админке.

Регистр направления здесь не важен: сравнение идёт по lower(), поэтому
объект с «Бетон» больше не выпадает из блока, как это было раньше.
"""
from django.db import migrations


def fill(apps, schema_editor):
    ProjectObject = apps.get_model('content', 'ProjectObject')
    for o in ProjectObject.objects.all():
        if o.segments:
            continue                      # руками уже проставлено — не трогаем
        segs = ['reshenie_kommercheskoe']  # раньше показывались все объекты
        d = (o.direction or '').strip().lower()
        if d == 'бетон':
            segs.append('reshenie_zastroyshchikam')
        elif d == 'опалубка':
            segs.append('reshenie_promyshlennost')
        o.segments = ','.join(segs)
        o.save(update_fields=['segments'])


def unfill(apps, schema_editor):
    ProjectObject = apps.get_model('content', 'ProjectObject')
    ProjectObject.objects.update(segments='')


class Migration(migrations.Migration):

    dependencies = [('content', '0010_projectobject_segments')]

    operations = [migrations.RunPython(fill, unfill)]
