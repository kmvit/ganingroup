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
