# -*- coding: utf-8 -*-
"""Калькуляторы: марки бетона с ценами и зоны доставки."""
from django.db import models

from core.models import Ordered


class ConcreteGrade(Ordered):
    """Марка бетона с ценой для калькулятора.

    Цена — «от», за 1 м³, без доставки: окончательная зависит от объёма,
    графика поставок и удалённости объекта. Точные цифры берутся из прайса
    и правятся здесь, без участия разработчика.
    """

    title = models.CharField('Марка', max_length=40, help_text='Например: М300')
    grade_class = models.CharField('Класс', max_length=40, blank=True,
                                   help_text='Например: В22,5 W4')
    price = models.PositiveIntegerField(
        'Цена от, ₽ за м³', null=True, blank=True,
        help_text='Без доставки. Пусто — вместо цены покажем «по запросу»')
    note = models.CharField('Примечание', max_length=200, blank=True)
    is_default = models.BooleanField('Выбрана по умолчанию', default=False)

    class Meta(Ordered.Meta):
        db_table = 'pages_concretegrade'
        verbose_name = 'Марка бетона и цена'
        verbose_name_plural = 'Марки бетона и цены'

    def __str__(self):
        return f'{self.title} — {self.price} ₽/м³' if self.price else f'{self.title} — по запросу'


class DeliveryZone(Ordered):
    """Зона доставки бетона: населённые пункты и тарифы из прайса.

    В прайсе три тарифа: маленький миксер (до 3 м³) и большой миксер —
    за рейс при объёме менее 5 м³ и за 1 м³ при объёме от 5 м³.
    """

    title = models.CharField('Населённые пункты', max_length=250,
                             help_text='Через запятую — как в прайсе')
    price_per_m3 = models.PositiveIntegerField(
        'От 5 м³ — цена за 1 м³, ₽', null=True, blank=True)
    price_trip = models.PositiveIntegerField(
        'До 5 м³ — цена за рейс, ₽', null=True, blank=True)
    price_trip_small = models.PositiveIntegerField(
        'Маленький миксер до 3 м³ — за рейс, ₽', null=True, blank=True,
        help_text='Справочно: применяется при ограниченном подъезде')

    class Meta(Ordered.Meta):
        db_table = 'pages_deliveryzone'
        verbose_name = 'Зона доставки'
        verbose_name_plural = 'Доставка по зонам'

    def __str__(self):
        return self.title
