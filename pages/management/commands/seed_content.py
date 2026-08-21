# -*- coding: utf-8 -*-
"""Первичное заполнение БД контентом, который сейчас в вёрстке.

Запуск:  python manage.py seed_content
Повторный запуск ничего не ломает: записи ищутся по ключевым полям (get_or_create).
Флаг --reset очищает контентные таблицы перед заливкой (заявки не трогает).
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from calc.models import ConcreteGrade, DeliveryZone
from content.models import (Department, Direction, Document, MapPoint, ProjectObject,
                            Review, Stat, TeamMember, TimelineEvent, Vacancy)
from core.models import Card, MenuItem, Page, SiteSettings
from pages.nav import MAIN as NAV_MAIN
from pages.seed_cards import CARDS
from pages.seed_cards_links import CARD_LINKS
from pages.seed_pages import PAGES_CONTENT

STATS = [
    ('150', 'тыс', 'м³ бетона и раствора в год', 'проектная мощность'),
    ('25', '', 'собственных автомиксеров', '+ 8 бетононасосов'),
    ('293', '', 'вида изделий ЖБИ', 'до 3 млн блоков в год'),
    ('60', '+', 'лет на рынке', 'база — КМВ'),
]

DIRECTIONS = [
    ('Бетон', 'Товарный бетон М100–М1000, спецмарки и растворы. Два узла, лаборатория.',
     'produkciya_beton', 'big', False),
    ('ЖБИ', '293 вида: ФБС, кольца, плиты, бордюры', 'produkciya_zhbi', '', False),
    ('Асфальт', 'Смеси по ГОСТ 9128-2009', 'produkciya_asfalt', '', False),
    ('Опалубка UPEX', 'Системы собственного производства. Расчёт комплекта и шеф-монтаж.',
     '', 'tall', True),
    ('Карьер', 'Щебень, песок природный, отсев', 'produkciya_inertnye', '', False),
    ('Транспорт', '25 миксеров · 8 насосов · самосвалы', 'logistika', '', False),
    ('Цемент', 'Фасованный — для мелкого опта', 'produkciya_cement', '', False),
    ('Лаборатория', 'Паспорт качества на каждую партию', 'laboratoriya', '', False),
]

OBJECTS = [
    ('ЖК «Название»', 'Ставрополь', 'бетон', '12 000 м³ за сезон — без срыва графика монолита'),
    ('Комплекс 24 этажа', 'Махачкала', 'опалубка', 'Комплект стеновой опалубки UPEX с шеф-монтажом'),
    ('Объект «Название»', 'КМВ', 'ЖБИ + бетон', 'Поставка ЖБИ и бетона из одних рук'),
    ('Участок трассы', 'Грозный', 'дорожное', 'Асфальтобетон и инертные с ритмичной подачей'),
    ('Производственный корпус', 'Пятигорск', 'промышленность',
     'Фундаменты под оборудование, спецмарки бетона'),
    ('ЖК «Название 2»', 'Ессентуки', 'бетон', 'Поставка с двух узлов, пиковые заливки по 400 м³'),
]

DEPARTMENTS = [
    'Приёмная', 'Диспетчерская бетона', 'Отдел опалубки UPEX',
    'Техподдержка для ГИПов', 'Отдел кадров', 'Бухгалтерия',
]

TEAM = [
    ('Имя Фамилия', 'директор по производству'),
    ('Имя Фамилия', 'руководитель направления бетон'),
    ('Имя Фамилия', 'руководитель UPEX'),
    ('Имя Фамилия', 'главный технолог, лаборатория'),
]

VACANCIES = [
    ('Водитель автомиксера', 'Штат',
     'график 5/2 и сменный · официальное оформление · автопарк группы'),
    ('Оператор бетонного завода', 'Штат',
     'смесительный узел Teka · сменный график · обучение'),
    ('Лаборант', 'Штат', 'аттестованная лаборатория · испытания бетона и материалов'),
]

TIMELINE = [
    ('19XX', 'Основание производства',
     'Запуск производственной площадки на Кавказских Минеральных Водах.'),
    ('19XX', 'Карьер и бетонный завод',
     'Открытие собственного карьера и выход на промышленные объёмы.'),
    ('20XX', 'Модернизация: Teka · ZENITH',
     'Немецкое смесительное и формовочное оборудование, собственная лаборатория.'),
    ('20XX', 'Запуск UPEX',
     'Собственное производство опалубочных систем — отгрузки по всей России.'),
    ('2026', 'Объединение под брендом ГАНИН ГРУПП',
     'Все направления — под единым зонтичным брендом. Один партнёр на весь монолит.'),
]

MAP_POINTS = [
    ('завод · КМВ', 16, 44, False),
    ('карьер', 11, 62, True),
    ('Ставрополь', 34, 30, False),
    ('Грозный', 46, 58, False),
    ('Махачкала', 60, 40, False),
]

REVIEW = ('«Для нас важнее всего был <em>ритм поставок</em> на пике сезона. График монолита '
          'мы не сорвали ни разу — поэтому и продолжаем работать вместе».',
          'Имя Фамилия', 'руководитель снабжения · застройщик')

# Цены из прайса «Бетоны и растворы», за 1 м³ без доставки.
# Класс переведён в марку по стандартному соответствию (В15 ≈ М200 и т.д.).
CONCRETE_GRADES = [
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

# Доставка из прайса: (зона, за рейс до 5 м³, за 1 м³ от 5 м³, маленький миксер за рейс)
DELIVERY_ZONES = [
    ('Пятигорск, Лермонтов, Винсады, Острогорка, Новый', 4751, 850, 5226),
    ('Ессентуки, ст. Ессентукская, Санамер, Садовый, Энергетик', 4751, 850, 5226),
    ('Капельница, Юца', 5362, 972, 5899),
    ('Железноводск, Белый Уголь, Железноводский', 5974, 1095, 6571),
    ('Горный, Бородыновка, Змейка', 5974, 1095, 6571),
    ('Минеральные Воды, ст. Суворовская, ст. Зольская', 6585, 1217, 7243),
    ('Кисловодск, Левокумка', 6585, 1217, 7243),
]

DOCUMENTS = [
    ('Паспорт качества на партию бетона', 'PDF', 'выдаётся на каждую отгрузку'),
    ('Сертификаты на ЖБИ', 'PDF', 'по каталогу изделий'),
    ('Реквизиты и карточка предприятия', 'PDF', 'для договорного отдела'),
]


class Command(BaseCommand):
    help = 'Заливает в базу контент, который сейчас зашит в вёрстку'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Очистить контентные таблицы перед заливкой')
        parser.add_argument('--if-empty', action='store_true',
                            help='Заливать только в пустую базу (для автостарта на сервере)')

    @transaction.atomic
    def handle(self, *args, **opts):
        # Общие данные и логотипы обновляем всегда: это безопасно —
        # уже загруженные заказчиком файлы не перезаписываются.
        s = SiteSettings.get()
        if not s.phone_main:
            s.phone_main = '+7 800 000-00-00'
        s.save()
        # логотипы из вёрстки — в админку, чтобы заказчик их видел и мог заменить
        logos = [
            ('logo_compact', 'logo-compact.svg'),
            ('logo_compact_light', 'logo-compact-dark.svg'),
            ('logo_full', 'logo.svg'),
            ('logo_full_light', 'logo-dark.svg'),
            ('logo_mark', 'logo-mark.svg'),
        ]
        src_dir = Path(settings.BASE_DIR) / 'static' / 'assets'
        loaded = 0
        for field, filename in logos:
            if getattr(s, field):
                continue                     # заказчик уже загрузил свой — не трогаем
            src = src_dir / filename
            if not src.exists():
                continue
            with src.open('rb') as fh:
                getattr(s, field).save(filename, File(fh), save=False)
            loaded += 1
        if loaded:
            s.save()
        self.stdout.write(f'  • общие данные сайта готовы (логотипов загружено: {loaded})')

        if opts['if_empty'] and Page.objects.exists():
            self.stdout.write('Контент уже есть — заливка пропущена.')
            return

        if opts['reset']:
            for model in (Stat, Direction, ProjectObject, Department, TeamMember,
                          Review, Vacancy, Document, TimelineEvent, MapPoint):
                model.objects.all().delete()
            MenuItem.objects.all().delete()
            Page.objects.all().delete()
            self.stdout.write(self.style.WARNING('Контентные таблицы очищены'))


        # --- меню ---
        for i, (key, label, url_name, children, ftitle) in enumerate(NAV_MAIN, 1):
            top, _ = MenuItem.objects.get_or_create(
                title=label, parent=None,
                defaults=dict(url_name=url_name or '', footer_title=ftitle, order=i * 10))
            for j, (ctitle, curl, cext) in enumerate(children or [], 1):
                MenuItem.objects.get_or_create(
                    title=ctitle, parent=top,
                    defaults=dict(url_name=curl or '', external_url='', order=j * 10))
        self.stdout.write(f'  • пунктов меню: {MenuItem.objects.count()}')

        # --- страницы ---
        for i, row in enumerate(PAGES_CONTENT):
            Page.objects.update_or_create(
                slug=row['slug'],
                defaults=dict(admin_title=row['admin_title'], h1=row['h1'],
                              subtitle=row['subtitle']),
            )
        self.stdout.write(f'  • страниц: {Page.objects.count()}')

        # --- плитки страниц ---
        pages_by_slug = {p.slug: p for p in Page.objects.all()}
        for slug, section, order, icon, title, text in CARDS:
            page_obj = pages_by_slug.get(slug)
            if not page_obj:
                continue
            Card.objects.get_or_create(
                page=page_obj, section=section, title=title,
                defaults=dict(icon=icon, text=text, order=order))
        for slug, section, order, icon, title, text, url_name, label in CARD_LINKS:
            page_obj = pages_by_slug.get(slug)
            if not page_obj:
                continue
            Card.objects.get_or_create(
                page=page_obj, section=section, title=title,
                defaults=dict(icon=icon, text=text, order=order,
                              url_name=url_name, link_label=label))
        self.stdout.write(f'  • плиток на страницах: {Card.objects.count()}')

        # --- сущности ---
        for i, (v, sup, label, note) in enumerate(STATS, 1):
            Stat.objects.get_or_create(label=label, defaults=dict(
                value=v, sup=sup, note=note, order=i * 10))

        for i, (title, tagline, url_name, size, is_upex) in enumerate(DIRECTIONS, 1):
            Direction.objects.get_or_create(title=title, defaults=dict(
                tagline=tagline, url_name=url_name, size=size, is_upex=is_upex, order=i * 10))

        for i, (title, city, direction, summary) in enumerate(OBJECTS, 1):
            ProjectObject.objects.get_or_create(title=title, defaults=dict(
                city=city, direction=direction, summary=summary,
                is_featured=(i <= 3), order=i * 10))

        for i, title in enumerate(DEPARTMENTS, 1):
            Department.objects.get_or_create(title=title, defaults=dict(
                person='Имя Фамилия', order=i * 10))

        for i, (name, position) in enumerate(TEAM, 1):
            TeamMember.objects.get_or_create(position=position, defaults=dict(
                name=name, order=i * 10))

        text, author, role = REVIEW
        Review.objects.get_or_create(author_role=role, defaults=dict(
            text=text, author=author, is_featured=True, order=10))

        for i, (title, kind, summary) in enumerate(VACANCIES, 1):
            Vacancy.objects.get_or_create(title=title, defaults=dict(
                kind=kind, summary=summary, order=i * 10))

        for i, (title, kind, summary) in enumerate(DOCUMENTS, 1):
            Document.objects.get_or_create(title=title, defaults=dict(
                kind=kind, summary=summary, order=i * 10))

        for i, (title, gclass, price, note) in enumerate(CONCRETE_GRADES, 1):
            ConcreteGrade.objects.get_or_create(title=title, defaults=dict(
                grade_class=gclass, price=price, note=note,
                is_default=(title == 'М300'), order=i * 10))

        for i, (title, trip, per_m3, small) in enumerate(DELIVERY_ZONES, 1):
            DeliveryZone.objects.get_or_create(title=title, defaults=dict(
                price_trip=trip, price_per_m3=per_m3, price_trip_small=small, order=i * 10))

        for i, (year, title, txt) in enumerate(TIMELINE, 1):
            TimelineEvent.objects.get_or_create(title=title, defaults=dict(
                year=year, text=txt, order=i * 10))

        for i, (title, left, top, is_own) in enumerate(MAP_POINTS, 1):
            MapPoint.objects.get_or_create(title=title, defaults=dict(
                left=left, top=top, is_own=is_own, order=i * 10))

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Цифры: {Stat.objects.count()}, направления: {Direction.objects.count()}, '
            f'объекты: {ProjectObject.objects.count()}, отделы: {Department.objects.count()}, '
            f'команда: {TeamMember.objects.count()}, вакансии: {Vacancy.objects.count()}, '
            f'история: {TimelineEvent.objects.count()}, карта: {MapPoint.objects.count()}, '
            f'документы: {Document.objects.count()}, отзывы: {Review.objects.count()}, '
            f'марки бетона: {ConcreteGrade.objects.count()}, '
            f'зоны доставки: {DeliveryZone.objects.count()}'))
