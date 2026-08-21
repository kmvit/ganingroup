# -*- coding: utf-8 -*-
"""Заливает типы конструкций для калькулятора.

Раньше они были зашиты в шаблон. Теперь правятся в админке, а сюда
переносятся в исходном виде — плюс «Фундамент» рядом с «Лентой».
"""
from django.db import migrations

BOX, CYL, HALF = 'box', 'cylinder', 'half'

# (название, значок, формула, подписи полей, количество, подсказка, по умолчанию)
TYPES = [
    ('Плита / стяжка', '▭', BOX, ('Длина', 'Ширина', 'Толщина'), False,
     'Объём = длина × ширина × толщина', True),
    ('Лента', '▯', BOX, ('Длина ленты', 'Ширина', 'Высота'), False,
     'Общая длина всех лент фундамента', False),
    ('Фундамент', '▤', BOX, ('Длина лент, суммарно', 'Ширина ленты', 'Высота'), False,
     'Ленточный фундамент: сложите длину всех лент, включая внутренние', False),
    ('Стена', '▮', BOX, ('Длина', 'Высота', 'Толщина'), False,
     'Проёмы (окна, двери) вычтите из длины', False),
    ('Колонна', '◫', BOX, ('Сторона A', 'Сторона B', 'Высота'), True,
     'Размеры сечения колонны и её высота', False),
    ('Свая', '◎', CYL, ('Диаметр', 'Глубина', ''), True,
     'Круглая свая: объём = π × (диаметр / 2)² × глубина', False),
    ('Лестница', '◺', HALF, ('Ширина марша', 'Длина проекции', 'Высота подъёма'), True,
     'Оценка по треугольному сечению марша — половина объёма', False),
]


def seed(apps, schema_editor):
    ConstructionType = apps.get_model('calc', 'ConstructionType')
    for i, (title, pic, formula, labels, count, hint, default) in enumerate(TYPES, 1):
        ConstructionType.objects.get_or_create(title=title, defaults=dict(
            pic=pic, formula=formula, label_a=labels[0], label_b=labels[1],
            label_c=labels[2], use_count=count, hint=hint, is_default=default,
            order=i * 10, published=True))


def unseed(apps, schema_editor):
    apps.get_model('calc', 'ConstructionType').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [('calc', '0002_constructiontype')]

    operations = [migrations.RunPython(seed, unseed)]
