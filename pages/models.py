# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.static import static
from django.utils.text import slugify


# ============================================================ ЗАЯВКИ

class Lead(models.Model):
    """Заявка «Запросить ТКП» — основная конверсия сайта."""

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=40)
    company = models.CharField('Компания', max_length=200, blank=True)
    details = models.TextField('Объект / объём / сроки', blank=True)
    page = models.CharField('Страница отправки', max_length=200, blank=True)
    created = models.DateTimeField('Создана', auto_now_add=True)
    processed = models.BooleanField('Обработана', default=False)

    class Meta:
        verbose_name = 'Заявка ТКП'
        verbose_name_plural = 'Заявки ТКП'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} · {self.phone}'


class HaulerLead(models.Model):
    """Заявка перевозчика (со своей техникой) — блок на странице «Карьера»."""

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=40)
    vehicles = models.CharField('Техника (тип · количество)', max_length=200, blank=True)
    created = models.DateTimeField('Создана', auto_now_add=True)
    processed = models.BooleanField('Обработана', default=False)

    class Meta:
        verbose_name = 'Заявка перевозчика'
        verbose_name_plural = 'Заявки перевозчиков'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} · {self.phone}'


# ============================================================ ОБЩИЕ ДАННЫЕ САЙТА

class SiteSettings(models.Model):
    """Общие данные сайта: логотипы, телефоны, почты, адреса, реквизиты.

    Запись всегда одна (синглтон) — правится в админке, подставляется во все страницы.
    Логотипы: если файл не загружен, используется исходный из вёрстки, поэтому
    сайт не может «остаться без логотипа».
    """

    # --- логотипы ---
    logo_full = models.ImageField('Логотип полный (для подвала, тёмный фон)',
                                  upload_to='logo/', blank=True)
    logo_full_light = models.ImageField('Логотип полный для светлой темы',
                                        upload_to='logo/', blank=True)
    logo_compact = models.ImageField('Логотип компактный (шапка, тёмный фон)',
                                     upload_to='logo/', blank=True)
    logo_compact_light = models.ImageField('Логотип компактный для светлой темы',
                                           upload_to='logo/', blank=True)
    logo_mark = models.ImageField('Знак (иконка вкладки)', upload_to='logo/', blank=True)

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


# ============================================================ БАЗА ДЛЯ КОНТЕНТА

class Ordered(models.Model):
    """Общее для контентных блоков: порядок вывода и публикация."""

    order = models.PositiveIntegerField('Порядок', default=100,
                                        help_text='Меньше — выше в списке')
    published = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        abstract = True
        ordering = ['order', 'id']


# ============================================================ СУЩНОСТИ

class Stat(Ordered):
    """Цифра холдинга: 150 000 м³ / 293 вида ЖБИ / 60+ лет."""

    value = models.CharField('Значение', max_length=30, help_text='Например: 150 или 293')
    sup = models.CharField('Приписка сверху', max_length=20, blank=True,
                           help_text='Например: 000 м³ — выводится мелким оранжевым')
    label = models.CharField('Подпись', max_length=200,
                             help_text='Например: м³ бетона и раствора в год')
    note = models.CharField('Уточнение', max_length=200, blank=True)

    class Meta(Ordered.Meta):
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
    photo = models.ImageField('Фото объекта', upload_to='objects/', blank=True)
    year = models.CharField('Год / период', max_length=40, blank=True)
    volume = models.CharField('Объём поставки', max_length=100, blank=True)
    is_featured = models.BooleanField('Показать на главной', default=False)

    class Meta(Ordered.Meta):
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)[:200] or 'obekt'
        super().save(*args, **kwargs)

    @property
    def meta_line(self):
        return ' · '.join(p for p in (self.city, self.direction) if p)


class Department(Ordered):
    """Отдел на странице «Контакты»: приёмная, диспетчерская, UPEX, кадры…"""

    title = models.CharField('Отдел', max_length=150)
    person = models.CharField('Сотрудник', max_length=150, blank=True)
    position = models.CharField('Должность', max_length=150, blank=True)
    phone = models.CharField('Телефон', max_length=40, blank=True)
    email = models.EmailField('E-mail', blank=True)
    photo = models.ImageField('Фото', upload_to='people/', blank=True)

    class Meta(Ordered.Meta):
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
        verbose_name = 'Событие истории'
        verbose_name_plural = 'История группы'

    def __str__(self):
        return f'{self.year} — {self.title}'


class MapPoint(Ordered):
    """Точка на карте присутствия: город поставки или своя площадка."""

    title = models.CharField('Город / площадка', max_length=120)
    left = models.PositiveIntegerField('Позиция слева, %', default=50,
                                       help_text='0–100 — где точка стоит на карте')
    top = models.PositiveIntegerField('Позиция сверху, %', default=50)
    is_own = models.BooleanField('Своя площадка (не просто поставка)', default=False)

    class Meta(Ordered.Meta):
        verbose_name = 'Точка на карте'
        verbose_name_plural = 'Карта присутствия'

    def __str__(self):
        return self.title


# ============================================================ СТРАНИЦЫ

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
        verbose_name = 'Страница (тексты и SEO)'
        verbose_name_plural = 'Страницы (тексты и SEO)'
        ordering = ['admin_title']

    def __str__(self):
        return self.admin_title

    @property
    def title_tag(self):
        return self.seo_title or self.h1 or self.admin_title


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
        verbose_name = 'Плитка на странице'
        verbose_name_plural = 'Плитки на страницах'

    def __str__(self):
        return f'{self.page.admin_title} · {self.title}'


# ============================================================ МЕНЮ

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
        verbose_name = 'Пункт меню'
        verbose_name_plural = 'Меню сайта'

    def __str__(self):
        return f'— {self.title}' if self.parent_id else self.title

    @property
    def href_key(self):
        """Ключ для шаблона: имя маршрута или внешняя ссылка."""
        return self.url_name or self.external_url or '#'


class VacancyApplication(models.Model):
    """Отклик на вакансию с резюме (страница «Карьера»)."""

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=40)
    vacancy = models.ForeignKey(Vacancy, verbose_name='Вакансия', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='applications')
    vacancy_title = models.CharField('Должность (текстом)', max_length=200, blank=True,
                                     help_text='Если вакансия выбрана не из списка')
    resume = models.FileField('Резюме', upload_to='resume/%Y-%m/', blank=True)
    comment = models.TextField('Комментарий', blank=True)
    created = models.DateTimeField('Получен', auto_now_add=True)
    processed = models.BooleanField('Обработан', default=False)

    class Meta:
        verbose_name = 'Отклик на вакансию'
        verbose_name_plural = 'Отклики на вакансии'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} · {self.vacancy or self.vacancy_title or "без вакансии"}'
