# -*- coding: utf-8 -*-
"""Содержание сайта: цифры, направления, объекты, люди, вакансии."""
from django.db import models

from core.models import Ordered
from content.utils import slugify_ru


class Stat(Ordered):
    """Цифра холдинга: 150 000 м³ / 293 вида ЖБИ / 60+ лет."""

    value = models.CharField('Значение', max_length=30, help_text='Например: 150 или 293')
    sup = models.CharField('Приписка сверху', max_length=20, blank=True,
                           help_text='Например: 000 м³ — выводится мелким оранжевым')
    label = models.CharField('Подпись', max_length=200,
                             help_text='Например: м³ бетона и раствора в год')
    note = models.CharField('Уточнение', max_length=200, blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_stat'
        verbose_name = 'Цифра холдинга'
        verbose_name_plural = 'Цифры холдинга'

    def __str__(self):
        return f'{self.value}{self.sup} — {self.label}'


class Direction(Ordered):
    """Направление группы: бетон, ЖБИ, асфальт, инертные, цемент, опалубка UPEX."""

    title = models.CharField('Название', max_length=120)
    tagline = models.CharField('Короткое описание', max_length=250, blank=True)
    photo = models.ImageField('Фото', upload_to='directions/', blank=True,
                              help_text='Если пусто — покажется серая плитка-заглушка')
    url_name = models.CharField('Маршрут страницы', max_length=60, blank=True,
                                help_text='Имя URL, например produkciya_beton. Пусто — плитка без ссылки')
    external_url = models.URLField('Внешняя ссылка', blank=True,
                                   help_text='Для UPEX — адрес отдельного сайта')
    size = models.CharField('Размер плитки', max_length=10, default='',
                            choices=[('', 'обычная'), ('big', 'большая'), ('tall', 'высокая')],
                            blank=True)
    is_upex = models.BooleanField('Это UPEX (особый стиль плитки)', default=False)

    class Meta(Ordered.Meta):
        db_table = 'pages_direction'
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления (продукция)'

    def __str__(self):
        return self.title


class ProjectObject(Ordered):
    """Реализованный объект: ЖК, дорога, промплощадка."""

    title = models.CharField('Название объекта', max_length=200)
    slug = models.SlugField('Адрес страницы', max_length=200, unique=True, blank=True)
    city = models.CharField('Город', max_length=100, blank=True)
    direction = models.CharField('Направление', max_length=100, blank=True,
                                 help_text='Например: бетон, опалубка, асфальт')
    summary = models.CharField('Кратко (в карточке)', max_length=250, blank=True)
    photo = models.ImageField('Фото объекта', upload_to='objects/', blank=True,
                              help_text='Обложка карточки и главное фото на странице кейса')
    year = models.CharField('Год / период', max_length=40, blank=True)
    volume = models.CharField('Объём поставки', max_length=100, blank=True)
    is_featured = models.BooleanField('Показать на главной', default=False)

    # --- страница кейса ---
    headline = models.CharField(
        'Заголовок кейса (H1)', max_length=250, blank=True,
        help_text='Крупный заголовок на странице объекта. Пусто — берётся название')
    context = models.TextField('Контекст', blank=True)
    challenge = models.TextField('Вызов', blank=True)
    solution = models.TextField('Решение', blank=True)
    result = models.TextField('Результат', blank=True)
    quote_text = models.TextField('Отзыв по объекту', blank=True,
                                  help_text='Часть можно выделить: <em>…</em>')
    quote_author = models.CharField('Автор отзыва', max_length=150, blank=True)
    quote_role = models.CharField('Должность / компания', max_length=200, blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_projectobject'
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_ru(self.title)[:200] or 'obekt'
        super().save(*args, **kwargs)

    @property
    def meta_line(self):
        return ' · '.join(p for p in (self.city, self.direction) if p)

    @property
    def case_rows(self):
        """Ряды блока «Как это было» — только заполненные."""
        return [(label, text) for label, text in (
            ('Контекст', self.context), ('Вызов', self.challenge),
            ('Решение', self.solution), ('Результат', self.result)) if text]

    @property
    def gallery(self):
        return self.gallery_photos.filter(published=True)


class ObjectStat(Ordered):
    """Цифра-плашка на странице кейса (20 тыс м³ / 24-7 / 0 срывов)."""

    project = models.ForeignKey(ProjectObject, verbose_name='Объект',
                                on_delete=models.CASCADE, related_name='stats')
    value = models.CharField('Значение', max_length=30, help_text='Например: 20 или 24/7')
    sup = models.CharField('Приписка сверху', max_length=20, blank=True,
                           help_text='Например: тыс — мелким оранжевым')
    label = models.CharField('Подпись', max_length=200, help_text='Например: м³ бетона поставлено')
    note = models.CharField('Уточнение', max_length=200, blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_objectstat'
        verbose_name = 'Цифра объекта'
        verbose_name_plural = 'Цифры объекта'

    def __str__(self):
        return f'{self.value}{self.sup} — {self.label}'


class ObjectPhoto(Ordered):
    """Фото в галерее объекта."""

    project = models.ForeignKey(ProjectObject, verbose_name='Объект',
                                on_delete=models.CASCADE, related_name='gallery_photos')
    image = models.ImageField('Фото', upload_to='objects/gallery/')
    caption = models.CharField('Подпись', max_length=200, blank=True,
                               help_text='Например: этап заливки — что видно на снимке')

    class Meta(Ordered.Meta):
        db_table = 'pages_objectphoto'
        verbose_name = 'Фото объекта'
        verbose_name_plural = 'Фото объекта'

    def __str__(self):
        return f'{self.project.title} · фото {self.pk}'


class CatalogItem(Ordered):
    """Позиция каталога продукции: марка бетона, изделие ЖБИ, смесь, фракция."""

    SECTIONS = [
        ('produkciya_beton', 'Бетон'),
        ('produkciya_zhbi', 'ЖБИ'),
        ('produkciya_asfalt', 'Асфальт'),
        ('produkciya_inertnye', 'Инертные материалы'),
    ]

    section = models.CharField('Раздел каталога', max_length=40, choices=SECTIONS)
    title = models.CharField('Название', max_length=200)
    chips = models.CharField('Бейджи', max_length=200, blank=True,
                             help_text='Короткие метки через « · », например: W4 · П3–П4')
    photo = models.ImageField('Фото', upload_to='catalog/', blank=True,
                              help_text='Если пусто — покажется серая плитка-заглушка')

    class Meta(Ordered.Meta):
        db_table = 'pages_catalogitem'
        verbose_name = 'Позиция каталога'
        verbose_name_plural = 'Каталог продукции'

    def __str__(self):
        return f'{self.get_section_display()} · {self.title}'

    @property
    def chip_list(self):
        return [c.strip() for c in self.chips.split('·') if c.strip()]


class Department(Ordered):
    """Отдел на странице «Контакты»: приёмная, диспетчерская, UPEX, кадры…"""

    title = models.CharField('Отдел', max_length=150)
    person = models.CharField('Сотрудник', max_length=150, blank=True)
    position = models.CharField('Должность', max_length=150, blank=True)
    phone = models.CharField('Телефон', max_length=40, blank=True)
    email = models.EmailField('E-mail', blank=True)
    photo = models.ImageField('Фото', upload_to='people/', blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_department'
        verbose_name = 'Отдел (контакты)'
        verbose_name_plural = 'Отделы (контакты)'

    def __str__(self):
        return self.title


class TeamMember(Ordered):
    """Руководитель направления — лица группы."""

    name = models.CharField('Имя и фамилия', max_length=150)
    position = models.CharField('Должность', max_length=200, blank=True)
    photo = models.ImageField('Фото', upload_to='people/', blank=True)
    is_featured = models.BooleanField('Показать на главной', default=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_teammember'
        verbose_name = 'Руководитель'
        verbose_name_plural = 'Команда'

    def __str__(self):
        return self.name


class Review(Ordered):
    """Отзыв заказчика. Слова в «эм» выделяются оранжевым подчёркиванием."""

    text = models.TextField('Текст отзыва',
                            help_text='Часть фразы можно выделить: обернуть в <em>…</em>')
    author = models.CharField('Автор', max_length=150, blank=True)
    author_role = models.CharField('Должность / компания', max_length=200, blank=True)
    photo = models.ImageField('Фото автора', upload_to='people/', blank=True)
    is_featured = models.BooleanField('Показать на главной', default=False)

    class Meta(Ordered.Meta):
        db_table = 'pages_review'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.author or "без автора"}: {self.text[:40]}…'


class Vacancy(Ordered):
    """Вакансия на странице «Карьера»."""

    title = models.CharField('Должность', max_length=200)
    kind = models.CharField('Метка', max_length=60, blank=True,
                            help_text='Например: производство, транспорт, офис')
    summary = models.CharField('Кратко', max_length=250, blank=True)
    salary = models.CharField('Зарплата', max_length=100, blank=True)
    description = models.TextField('Описание', blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_vacancy'
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

    def __str__(self):
        return self.title


class Document(Ordered):
    """Документ: сертификат, паспорт качества, реквизиты."""

    title = models.CharField('Название', max_length=200)
    kind = models.CharField('Тип', max_length=40, blank=True,
                            help_text='Например: PDF, DOC')
    summary = models.CharField('Пояснение', max_length=250, blank=True)
    file = models.FileField('Файл', upload_to='docs/', blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_document'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def __str__(self):
        return self.title


class TimelineEvent(Ordered):
    """Событие в истории группы (страница «О группе»)."""

    year = models.CharField('Год', max_length=40)
    title = models.CharField('Событие', max_length=200)
    text = models.TextField('Описание', blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_timelineevent'
        verbose_name = 'Событие истории'
        verbose_name_plural = 'История группы'

    def __str__(self):
        return f'{self.year} — {self.title}'


class MapPoint(Ordered):
    """Точка на карте присутствия: город поставки или своя площадка.

    lat/lng — для настоящей Яндекс.Карты (с API-ключом). left/top — запасная
    схематичная карта, когда ключа нет.
    """

    title = models.CharField('Город / площадка', max_length=120)
    lat = models.FloatField('Широта', null=True, blank=True,
                            help_text='Например 44.0610 (для Яндекс.Карты). '
                                      'Координаты можно скопировать из Яндекс.Карт: '
                                      'правый клик по точке → «Что здесь?»')
    lng = models.FloatField('Долгота', null=True, blank=True,
                            help_text='Например 42.9868')
    left = models.PositiveIntegerField('Позиция слева, %', default=50,
                                       help_text='0–100 — для схематичной карты без ключа')
    top = models.PositiveIntegerField('Позиция сверху, %', default=50)
    is_own = models.BooleanField('Своя площадка (завод, карьер)', default=False,
                                 help_text='Отмечается крупной оранжевой меткой')

    class Meta(Ordered.Meta):
        db_table = 'pages_mappoint'
        verbose_name = 'Точка на карте'
        verbose_name_plural = 'Карта присутствия'

    def __str__(self):
        return self.title
