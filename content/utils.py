# -*- coding: utf-8 -*-
"""Утилиты контента. Без импорта моделей — безопасно для миграций."""

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def slugify_ru(text):
    """Латинский слаг из русского текста: «МКЦ Россия» → mkc-rossiya."""
    from django.utils.text import slugify
    latin = ''.join(_TRANSLIT.get(c, c) for c in (text or '').lower())
    return slugify(latin)


def safe_reverse(url_name):
    """Адрес по имени маршрута; '' — если имени нет или страница убрана."""
    from django.urls import NoReverseMatch, reverse
    if not url_name:
        return ''
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return ''


# Разделы продающего сайта: каталог и цены по направлениям живут там.
# Запасной вариант, если в «Направлениях» внешняя ссылка не задана.
SD2_URLS = {
    'produkciya_beton': 'https://sd2-kmv.ru/cena-betona-s-dostavkoj',
    'produkciya_zhbi': 'https://sd2-kmv.ru/ZHB-zavod-ZHBI',
    'produkciya_asfalt': 'https://sd2-kmv.ru/asfaltobeton',
    'produkciya_inertnye': 'https://sd2-kmv.ru/karer-shchebnya-i-peska',
}
