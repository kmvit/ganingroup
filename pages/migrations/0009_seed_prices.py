# -*- coding: utf-8 -*-
"""Заливает цены и зоны доставки в уже работающую базу.

Команда seed_content на сервере запускается с --if-empty и на непустой базе
выходит сразу, поэтому новые справочники сами бы не появились. Здесь данные
создаются один раз при обновлении; существующие записи не трогаются.
"""
import datetime

from django.db import migrations

# Цены из прайса «Бетоны и растворы» от 18.07.2026, за 1 м³ без доставки.
GRADES = [
    ('М100', 'В7,5 W4', 5076, ''),
    ('М150', 'В12,5 W4', 5355, ''),
    ('М200', 'В15 W4', 5596, ''),
    ('М250', 'В20 W4', 5736, ''),
    ('М300', 'В22,5 W4', 6015, ''),
    ('М350', 'В25 W4', 6200, ''),
    ('М400', 'В30 W6-8', 7100, 'пластичность П4'),
    ('М450', 'В35 W6-8', 8320, 'высокомарочный'),
    ('М550', 'В40 W6-8', 8785, 'высокомарочный'),
    ('М600', 'В45 W6-8', 10180, 'высокомарочный'),
    ('спецмарка', '', None, 'подбирает технолог по проекту'),
]

# (зона, за рейс до 5 м³, за 1 м³ от 5 м³, маленький миксер за рейс)
ZONES = [
    ('Пятигорск, Лермонтов, Винсады, Острогорка, Новый', 4751, 850, 5226),
    ('Ессентуки, ст. Ессентукская, Санамер, Садовый, Энергетик', 4751, 850, 5226),
    ('Капельница, Юца', 5362, 972, 5899),
    ('Железноводск, Белый Уголь, Железноводский', 5974, 1095, 6571),
    ('Горный, Бородыновка, Змейка', 5974, 1095, 6571),
    ('Минеральные Воды, ст. Суворовская, ст. Зольская', 6585, 1217, 7243),
    ('Кисловодск, Левокумка', 6585, 1217, 7243),
]

PRICE_DATE = datetime.date(2026, 7, 18)


def seed(apps, schema_editor):
    ConcreteGrade = apps.get_model('pages', 'ConcreteGrade')
    DeliveryZone = apps.get_model('pages', 'DeliveryZone')
    SiteSettings = apps.get_model('pages', 'SiteSettings')

    for i, (title, gclass, price, note) in enumerate(GRADES, 1):
        ConcreteGrade.objects.get_or_create(title=title, defaults=dict(
            grade_class=gclass, price=price, note=note,
            is_default=(title == 'М300'), order=i * 10, published=True))

    for i, (title, trip, per_m3, small) in enumerate(ZONES, 1):
        DeliveryZone.objects.get_or_create(title=title, defaults=dict(
            price_trip=trip, price_per_m3=per_m3, price_trip_small=small,
            order=i * 10, published=True))

    s = SiteSettings.objects.first()
    if s and not s.price_valid_from:
        s.price_valid_from = PRICE_DATE
        s.save(update_fields=['price_valid_from'])


def unseed(apps, schema_editor):
    """Откат: справочники удаляем, чтобы миграция была обратимой."""
    apps.get_model('pages', 'ConcreteGrade').objects.all().delete()
    apps.get_model('pages', 'DeliveryZone').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [('pages', '0008_deliveryzone')]

    operations = [migrations.RunPython(seed, unseed)]
