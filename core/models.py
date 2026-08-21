# -*- coding: utf-8 -*-
"""Основа сайта: общие данные, меню, страницы и плитки."""
import re

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.templatetags.static import static
from django.utils.html import strip_tags


LOGO_EXT = FileExtensionValidator(
    allowed_extensions=['svg', 'png', 'jpg', 'jpeg', 'webp'],
    message='Логотип принимаем в SVG, PNG, JPG или WEBP.')


class Ordered(models.Model):
    """Общее для контентных блоков: порядок вывода и публикация."""

    order = models.PositiveIntegerField('Порядок', default=100,
                                        help_text='Меньше — выше в списке')
    published = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        abstract = True
        ordering = ['order', 'id']


class SiteSettings(models.Model):
    """Общие данные сайта: логотипы, телефоны, почты, адреса, реквизиты.

    Запись всегда одна (синглтон) — правится в админке, подставляется во все страницы.
    Логотипы: если файл не загружен, используется исходный из вёрстки, поэтому
    сайт не может «остаться без логотипа».
    """

    # --- логотипы ---
    # FileField, а не ImageField: логотипы векторные (SVG), а проверка картинок
    # через Pillow такие файлы отклоняет. Расширения ограничены валидатором.
    logo_full = models.FileField('Логотип полный (для подвала, тёмный фон)',
                            upload_to='logo/', blank=True,
                            validators=[LOGO_EXT])
    logo_full_light = models.FileField('Логотип полный для светлой темы',
                            upload_to='logo/', blank=True,
                            validators=[LOGO_EXT])
    logo_compact = models.FileField('Логотип компактный (шапка, тёмный фон)',
                            upload_to='logo/', blank=True,
                            validators=[LOGO_EXT])
    logo_compact_light = models.FileField('Логотип компактный для светлой темы',
                            upload_to='logo/', blank=True,
                            validators=[LOGO_EXT])
    logo_mark = models.FileField('Знак (иконка вкладки)',
                            upload_to='logo/', blank=True,
                            validators=[LOGO_EXT])

    # --- телефоны ---
    phone_main = models.CharField('Телефон основной', max_length=40, default='+7 800 000-00-00')
    phone_dispatch = models.CharField('Диспетчерская бетона', max_length=40, blank=True)
    phone_upex = models.CharField('Отдел опалубки UPEX', max_length=40, blank=True)

    # --- почта ---
    email_main = models.EmailField('E-mail основной', blank=True)
    email_sales = models.EmailField('E-mail отдела продаж', blank=True)
    email_hr = models.EmailField('E-mail отдела кадров', blank=True)

    # --- адреса ---
    address_office = models.CharField('Адрес офиса', max_length=250, blank=True)
    address_plant = models.CharField('Адрес завода', max_length=250, blank=True)
    address_quarry = models.CharField('Адрес карьера', max_length=250, blank=True)
    work_hours = models.CharField('Режим работы', max_length=150, blank=True,
                                  help_text='Например: пн–сб 8:00–18:00, в сезон — круглосуточно')

    # --- бренд и реквизиты ---
    slogan = models.CharField('Слоган', max_length=150, default='Строим основу будущего.')
    founded_year = models.PositiveIntegerField('Год основания', null=True, blank=True,
                                               help_text='Подставляется в текст «С … года поставляем бетон…»')
    legal_name = models.CharField('Юридическое лицо', max_length=250,
                                  default='ЗАО «Стройдеталь-2»')
    copyright_note = models.CharField('Приписка в копирайте', max_length=250, blank=True,
                                      default='ГАНИН ГРУПП — маркетинговый бренд группы.')
    footer_about = models.TextField(
        'Текст в подвале под логотипом', blank=True,
        default='Бетон, ЖБИ, асфальт, опалубка, карьер, транспорт — под единым брендом. '
                'База на КМВ, поставки по СКФО и всей России.')

    # --- внешние ссылки ---
    upex_url = models.URLField('Сайт опалубки UPEX', blank=True,
                               help_text='Ссылка в меню «Опалубка (UPEX) ↗»')
    messenger_url = models.CharField('Ссылка мессенджера (кнопка MAX)', max_length=250, blank=True)

    # --- цены ---
    price_note = models.CharField(
        'Оговорка про цены', max_length=300, blank=True,
        default='Окончательная стоимость зависит от объёма, графика поставок '
                'и удалённости объекта.',
        help_text='Показывается под результатом калькулятора. Фраза про доставку '
                  'добавляется автоматически — в зависимости от того, выбрал её клиент или нет')
    price_valid_from = models.DateField(
        'Цены действуют с', null=True, blank=True,
        help_text='Дата из прайс-листа — выводится рядом с результатом')

    # --- уведомления о заявках ---
    notify_emails = models.CharField(
        'Куда слать заявки (почта)', max_length=400, blank=True,
        help_text='Один или несколько адресов через запятую. Пусто — письма не отправляются')
    telegram_token = models.CharField(
        'Токен телеграм-бота', max_length=200, blank=True,
        help_text='Получить у @BotFather. Пусто — в телеграм не отправляется')
    telegram_chat_id = models.CharField(
        'ID чата в телеграме', max_length=100, blank=True,
        help_text='Куда бот пришлёт заявку: ваш ID или ID группы')

    @property
    def notify_email_list(self):
        return [e.strip() for e in self.notify_emails.split(',') if e.strip()]

    class Meta:
        db_table = 'pages_sitesettings'
        verbose_name = 'Общие данные сайта'
        verbose_name_plural = 'Общие данные сайта'

    def __str__(self):
        return 'Общие данные сайта'

    def save(self, *args, **kwargs):
        self.pk = 1          # всегда одна запись
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Общие данные сайта удалять нельзя — их можно только править.')

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # --- логотипы с откатом на файлы вёрстки ---
    def _logo(self, field, fallback):
        f = getattr(self, field)
        return f.url if f else static(fallback)

    @property
    def logo_full_url(self):
        return self._logo('logo_full', 'assets/logo.svg')

    @property
    def logo_full_light_url(self):
        return self._logo('logo_full_light', 'assets/logo-dark.svg')

    @property
    def logo_compact_url(self):
        return self._logo('logo_compact', 'assets/logo-compact.svg')

    @property
    def logo_compact_light_url(self):
        return self._logo('logo_compact_light', 'assets/logo-compact-dark.svg')

    @property
    def logo_mark_url(self):
        return self._logo('logo_mark', 'assets/logo-mark.svg')

    @property
    def phone_link(self):
        """Телефон в виде tel:+7900… — только цифры и плюс."""
        digits = ''.join(ch for ch in self.phone_main if ch.isdigit())
        return '+' + digits if digits else ''


class MenuItem(Ordered):
    """Пункт меню. Дерево на два уровня: раздел и его подпункты.

    Из этой же структуры собираются шапка, подвал и мобильное меню,
    поэтому пункты не могут разойтись между собой.
    """

    title = models.CharField('Название', max_length=120)
    parent = models.ForeignKey('self', verbose_name='Раздел', null=True, blank=True,
                               on_delete=models.CASCADE, related_name='children',
                               help_text='Пусто — пункт верхнего уровня')
    url_name = models.CharField('Маршрут', max_length=60, blank=True,
                                help_text='Имя URL, например produkciya_beton')
    external_url = models.URLField('Внешняя ссылка', blank=True,
                                   help_text='Если ведёт на другой сайт (UPEX)')
    footer_title = models.CharField('Заголовок колонки в подвале', max_length=120, blank=True,
                                    help_text='Если пусто — берётся название. '
                                              '«Продукция» в подвале называется «Направления»')
    show_in_footer = models.BooleanField('Показывать в подвале', default=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_menuitem'
        verbose_name = 'Пункт меню'
        verbose_name_plural = 'Меню сайта'

    def __str__(self):
        return f'— {self.title}' if self.parent_id else self.title

    @property
    def href_key(self):
        """Ключ для шаблона: имя маршрута или внешняя ссылка."""
        return self.url_name or self.external_url or '#'


class Page(models.Model):
    """Тексты и SEO конкретной страницы.

    Привязка по `slug` = имя маршрута (например produkciya_beton).
    Страницы создаются командой `seed_content`, в админке их правят, но не добавляют:
    набор страниц задан вёрсткой.
    """

    slug = models.CharField('Маршрут', max_length=60, unique=True,
                            help_text='Имя URL — менять не нужно')
    admin_title = models.CharField('Страница', max_length=120,
                                   help_text='Как называется в этом списке')
    h1 = models.CharField('Заголовок на странице (H1)', max_length=250, blank=True)
    subtitle = models.TextField('Подзаголовок / вводный текст', blank=True)
    body = models.TextField('Основной текст', blank=True,
                            help_text='Для текстовых страниц — политика, согласие. Можно с HTML')
    seo_title = models.CharField('SEO-заголовок (title)', max_length=250, blank=True,
                                 help_text='Если пусто — берётся заголовок страницы')
    seo_description = models.TextField('SEO-описание (description)', blank=True, max_length=400)

    class Meta:
        db_table = 'pages_page'
        verbose_name = 'Страница (тексты и SEO)'
        verbose_name_plural = 'Страницы (тексты и SEO)'
        ordering = ['admin_title']

    def __str__(self):
        return self.admin_title

    @property
    def title_tag(self):
        """Заголовок вкладки и поисковой выдачи.

        h1 хранится с разметкой (<br>, <em>) ради дизайна, но в <title>
        теги не рендерятся — поэтому здесь их убираем.
        """
        if self.seo_title:
            return self.seo_title
        # <br> заменяем пробелом, иначе слова склеиваются
        text = re.sub(r'<br\s*/?>', ' ', self.h1 or '')
        return re.sub(r'\s+', ' ', strip_tags(text)).strip() or self.admin_title


class Card(Ordered):
    """Плитка на странице: иконка/индекс, заголовок, текст, ссылка.

    Один тип блока закрывает большинство сеток вёрстки (их около 97 на 14 страницах),
    поэтому заказчик правит их в одном привычном виде.
    """

    page = models.ForeignKey(Page, verbose_name='Страница', on_delete=models.CASCADE,
                             related_name='cards')
    section = models.CharField('Блок на странице', max_length=60, default='main',
                              help_text='Ключ секции — если на странице несколько сеток')
    icon = models.CharField('Индекс / иконка', max_length=20, blank=True,
                            help_text='Короткая подпись в квадрате, например 01 или ↗')
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст', blank=True)
    url_name = models.CharField('Маршрут ссылки', max_length=60, blank=True,
                                help_text='Имя URL, если плитка ведёт на страницу')
    link_label = models.CharField('Подпись ссылки', max_length=100, blank=True)

    class Meta(Ordered.Meta):
        db_table = 'pages_card'
        verbose_name = 'Плитка на странице'
        verbose_name_plural = 'Плитки на страницах'

    def __str__(self):
        return f'{self.page.admin_title} · {self.title}'
