# -*- coding: utf-8 -*-
"""Навигация сайта.

Пункты хранятся в админке (модель MenuItem) и собираются из одного дерева,
поэтому шапка, подвал и мобильное меню не могут разойтись.
Структура ниже — исходная из вёрстки: используется для первичного заполнения
(команда seed_content) и как запасной вариант, если меню в базе пустое.
"""

RESHENIYA = [
    ('Застройщикам ЖК', 'reshenie_zastroyshchikam', None),
    ('Коммерческая стройка', 'reshenie_kommercheskoe', None),
    ('Дорожникам', 'reshenie_dorozhnikam', None),
    ('Промышленность', 'reshenie_promyshlennost', None),
    ('Частная застройка', 'reshenie_chastnaya_zastroyka', None),
]

PRODUKCIYA = [
    ('Бетон', 'produkciya_beton', None),
    ('ЖБИ', 'produkciya_zhbi', None),
    ('Асфальт', 'produkciya_asfalt', None),
    ('Опалубка (UPEX) ↗', None, '#'),
    ('Инертные материалы', 'produkciya_inertnye', None),
    ('Фасованный цемент', 'produkciya_cement', None),
]

USLUGI = [
    ('Логистика', 'logistika', None),
    ('Расчёт опалубки', 'raschet_opalubki', None),
    ('Шеф-монтаж', 'shef_montazh', None),
    ('Лаборатория', 'laboratoriya', None),
]

# (ключ, название, маршрут, подпункты, заголовок колонки в подвале)
MAIN = [
    ('o_gruppe', 'О группе', 'o_gruppe', None, ''),
    ('resheniya', 'Решения', 'resheniya', RESHENIYA, 'Решения'),
    ('produkciya', 'Продукция', 'produkciya', PRODUKCIYA, 'Направления'),
    ('uslugi', 'Сервисы', 'uslugi', USLUGI, 'Сервисы'),
    ('obekty', 'Объекты', 'obekty', None, ''),
    ('kariera', 'Карьера', 'kariera', None, ''),
    ('kontakty', 'Контакты', 'kontakty', None, ''),
]

COMPANY_COLUMN = 'Компания'      # колонка подвала из пунктов без подменю


def _item(title, url_name, external):
    return {'label': title, 'url_name': url_name or '', 'external': external or ''}


def _from_db(upex_url=''):
    """Собрать навигацию из админки. None — если меню ещё не заполнено."""
    from core.models import MenuItem

    tops = list(MenuItem.objects.filter(parent__isnull=True, published=True)
                .prefetch_related('children'))
    if not tops:
        return None

    def kids(top):
        return [_item(c.title, c.url_name,
                      upex_url if (upex_url and not c.url_name) else c.external_url)
                for c in top.children.all() if c.published]

    main, footer, mmenu = [], [], []
    plain = []       # пункты верхнего уровня без подменю — колонка «Компания»
    for top in tops:
        children = kids(top)
        main.append({'key': top.url_name or top.title, 'label': top.title,
                     'url_name': top.url_name, 'children': children or None})
        if children:
            if top.show_in_footer:
                footer.append({'title': top.footer_title or top.title, 'items': children})
            mmenu.append({'title': top.title, 'items': children})
        elif top.show_in_footer:
            plain.append(_item(top.title, top.url_name, top.external_url))
    if plain:
        footer.append({'title': COMPANY_COLUMN, 'items': plain})
    return main, footer, mmenu


def _from_code(upex_url=''):
    """Запасной вариант — структура из вёрстки."""
    def items(rows):
        return [_item(t, u, upex_url if (upex_url and e) else e) for t, u, e in rows]

    main = [{'key': key, 'label': label, 'url_name': url,
             'children': items(children) if children else None}
            for key, label, url, children, _ in MAIN]
    footer = [{'title': ftitle or label, 'items': items(children)}
              for key, label, url, children, ftitle in MAIN if children]
    footer.append({'title': COMPANY_COLUMN,
                   'items': [_item(label, url, None)
                             for key, label, url, children, _ in MAIN if not children]})
    mmenu = [{'title': label, 'items': items(children)}
             for key, label, url, children, _ in MAIN if children]
    return main, footer, mmenu


_ASSET_V = None


def _asset_version():
    """Версия статики = короткий хеш содержимого site.css. Меняется всегда, когда
    меняется CSS (в отличие от mtime, который при пересборке мог не обновляться) →
    браузер гарантированно берёт свежий файл, а не старый из 30-дневного кэша."""
    global _ASSET_V
    if _ASSET_V is not None:
        return _ASSET_V
    import hashlib

    from django.conf import settings
    for base in [settings.BASE_DIR / 'static', settings.STATIC_ROOT]:
        try:
            data = (base / 'assets' / 'site.css').read_bytes()
            _ASSET_V = hashlib.md5(data).hexdigest()[:10]
            return _ASSET_V
        except OSError:
            continue
    _ASSET_V = '1'
    return _ASSET_V


def nav(request):
    """Контекст-процессор: навигация и общие данные сайта — во всех шаблонах."""
    from core.models import SiteSettings

    site = SiteSettings.get()
    upex = site.upex_url
    built = _from_db(upex) or _from_code(upex)
    main, footer, mmenu = built
    return {
        'site': site,
        'nav_main': main,
        'nav_footer': footer,
        'nav_mmenu': mmenu,
        'phone': site.phone_link,
        'phone_label': site.phone_main,
        'asset_v': _asset_version(),
    }
