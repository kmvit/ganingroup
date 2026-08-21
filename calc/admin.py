# -*- coding: utf-8 -*-
"""Админка: калькуляторы и цены."""
from django.contrib import admin

from .models import ConcreteGrade, ConstructionType, DeliveryZone


@admin.register(ConcreteGrade)
class ConcreteGradeAdmin(admin.ModelAdmin):
    """Цены для калькулятора: «от», за 1 м³, без доставки."""
    list_display = ('title', 'grade_class', 'price', 'is_default', 'order', 'published')
    list_editable = ('price', 'is_default', 'order', 'published')
    list_display_links = ('title',)


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    """Тарифы доставки по прайсу: до 5 м³ — за рейс, от 5 м³ — за м³."""
    list_display = ('title', 'price_trip', 'price_per_m3', 'price_trip_small',
                    'order', 'published')
    list_editable = ('price_trip', 'price_per_m3', 'price_trip_small', 'order', 'published')
    list_display_links = ('title',)


@admin.register(ConstructionType)
class ConstructionTypeAdmin(admin.ModelAdmin):
    """Типы конструкций в калькуляторе. Формулы заданы в коде — здесь выбор одной из трёх."""
    list_display = ('title', 'pic', 'formula', 'use_count', 'is_default', 'order', 'published')
    list_editable = ('order', 'published', 'is_default')
    list_display_links = ('title',)
    fieldsets = (
        (None, {'fields': ('title', 'pic', 'hint')}),
        ('Расчёт', {'fields': ('formula', 'label_a', 'label_b', 'label_c', 'use_count')}),
        ('Показ', {'fields': ('is_default', 'order', 'published')}),
    )
