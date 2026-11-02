# -*- coding: utf-8 -*-
"""Админка: общие данные, меню и страницы."""
from django import forms
from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html

from .models import Card, MenuItem, Page, PagePhoto, SiteSettings

admin.site.site_header = 'ГАНИН ГРУПП — управление сайтом'
admin.site.site_title = 'ГАНИН ГРУПП'
admin.site.index_title = 'Что можно изменить на сайте'


def photo_preview(obj, field='photo', height=44):
    f = getattr(obj, field, None)
    if not f:
        return '—'
    return format_html('<img src="{}" style="height:{}px;border:1px solid #ddd" />', f.url, height)


class PhotoMixin:
    @admin.display(description='Фото')
    def preview(self, obj):
        return photo_preview(obj)


class MenuChildInline(admin.TabularInline):
    """Подпункты правятся внутри своего раздела."""
    model = MenuItem
    fk_name = 'parent'
    extra = 0
    fields = ('title', 'page', 'url_name', 'external_url', 'order', 'published')
    verbose_name = 'Подпункт'
    verbose_name_plural = 'Подпункты меню'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'page':
            kwargs['queryset'] = Page.objects.filter(
                Q(product_slug__isnull=False) | Q(slug='produkciya_mineralnyy_poroshok'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CardInline(admin.TabularInline):
    """Плитки правятся прямо внутри своей страницы."""
    model = Card
    extra = 0
    fields = ('section', 'icon', 'title', 'text', 'photo', 'url_name', 'link_label', 'order', 'published')
    ordering = ('section', 'order')


class PagePhotoInline(admin.TabularInline):
    """Галерея страницы: фото кейса, галерея карточки товара."""
    model = PagePhoto
    extra = 0
    fields = ('image', 'caption', 'order', 'published')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Одна запись на весь сайт — добавлять и удалять нельзя, только править."""

    fieldsets = (
        ('Первый экран главной', {
            'description': 'Фоновое видео (MP4/WEBM, без звука) и фото-замена. '
                           'Пока файлы не загружены — показывается заглушка вёрстки.',
            'fields': ('hero_video', 'hero_photo'),
        }),
        ('Логотипы', {
            'description': 'Если файл не загружен — используется логотип из вёрстки. '
                           'Нужны версии для тёмного и светлого оформления.',
            'fields': ('logo_compact', 'logo_compact_light', 'logo_full',
                       'logo_full_light', 'logo_mark'),
        }),
        ('Телефоны', {'fields': ('phone_main', 'phone_dispatch', 'phone_upex')}),
        ('Почта', {'fields': ('email_main', 'email_sales', 'email_hr')}),
        ('Адреса и режим работы', {
            'fields': ('address_office', 'address_plant', 'address_quarry', 'work_hours'),
        }),
        ('Карта', {'fields': ('map_api_key', 'delivery_radius_km', 'map_embed_url')}),
        ('Индексация в поиске', {
            'description': 'Пока сайт готовится / до перехода на рабочий домен — '
                           'держите галочку включённой. При запуске снимите её.',
            'fields': ('noindex',),
        }),
        ('Бренд и реквизиты', {
            'fields': ('slogan', 'founded_year', 'legal_name', 'requisites',
                       'copyright_note', 'footer_about'),
        }),
        ('Внешние ссылки', {'fields': ('upex_url', 'messenger_url')}),
        ('Цены', {
            'description': 'Оговорка и дата прайса — показываются в калькуляторе. '
                           'Сами цены задаются в разделе «Марки бетона и цены».',
            'fields': ('price_note', 'price_valid_from'),
        }),
        ('Уведомления о заявках', {
            'description': 'Куда сообщать о новых заявках. Если поля пустые — '
                           'заявки всё равно сохраняются и видны в разделах ниже.',
            'fields': ('notify_emails', 'telegram_token', 'telegram_chat_id'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'url_name', 'order', 'published', 'show_in_footer')
    list_editable = ('order', 'published', 'show_in_footer')
    list_display_links = ('title',)
    list_filter = ('published', 'parent')
    inlines = [MenuChildInline]
    fieldsets = (
        (None, {'fields': ('title', 'parent')}),
        ('Куда ведёт', {'fields': ('page', 'url_name', 'external_url')}),
        ('Показ', {'fields': ('footer_title', 'show_in_footer', 'order', 'published')}),
    )

    def get_queryset(self, request):
        # в списке показываем разделы верхнего уровня и подпункты вместе, но сортировкой по дереву
        return super().get_queryset(request).select_related('parent')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'page':
            kwargs['queryset'] = Page.objects.filter(
                Q(product_slug__isnull=False) | Q(slug='produkciya_mineralnyy_poroshok'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# «Фото страницы» реально выводится не на всех страницах — только там, где в вёрстке
# есть под него место. Для каждой такой страницы — своя подсказка, что это за фото.
PAGE_PHOTO_HINT = {
    'o_gruppe': 'Портрет собственника в блоке «Слово собственника».',
    'reshenie_zastroyshchikam': 'Фоновое фото в шапке страницы (за заголовком).',
    'reshenie_kommercheskoe':   'Фоновое фото в шапке страницы (за заголовком).',
    'reshenie_dorozhnikam':     'Фоновое фото в шапке страницы (за заголовком).',
    'reshenie_promyshlennost':  'Фоновое фото в шапке страницы (за заголовком).',
    'reshenie_chastnaya_zastroyka': 'Фоновое фото в шапке страницы (за заголовком).',
    'obekt':      'Главное фото кейса в шапке (съёмка с дрона). Снимки объекта — в галерее ниже.',
    'logistika':  'Фото слева в блоке «Что вы получаете» (автопарк).',
    'raschet_opalubki': 'Фото слева в блоке «Что вы получаете» (инженер за расчётом).',
    'shef_montazh':     'Фото слева в блоке «Что вы получаете» (шеф-монтаж на площадке).',
    'laboratoriya':     'Фото слева в блоке «Что вы получаете» (лаборатория).',
}
# Галерея (PagePhoto) есть только у кейса.
PAGE_GALLERY_SLUGS = {'obekt'}
# Страницы убраны с сайта (направления ушли на sd2-kmv.ru) — в админке не показываем,
# записи в базе остаются на случай возврата.
RETIRED_PAGE_SLUGS = {'produkciya_beton', 'produkciya_zhbi', 'produkciya_asfalt',
                      'produkciya_inertnye', 'produkciya_kartochka'}


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    class PageForm(forms.ModelForm):
        class Meta:
            model = Page
            fields = '__all__'

        def clean_product_slug(self):
            value = self.cleaned_data.get('product_slug')
            if not self.instance.pk and not value:
                raise forms.ValidationError('Укажите адрес новой страницы продукции.')
            if value in {'cement', 'beton', 'beton-m350', 'zhbi', 'asfalt', 'inertnye',
                         'mineralnyy-poroshok'}:
                raise forms.ValidationError('Этот адрес уже используется на сайте.')
            return value

    form = PageForm
    list_display = ('admin_title', 'h1', 'slug', 'has_seo')
    search_fields = ('admin_title', 'h1', 'subtitle', 'body')
    readonly_fields = ('slug',)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(slug__in=RETIRED_PAGE_SLUGS)

    def get_inline_instances(self, request, obj=None):
        # плитки — у всех, галерея — только там, где она выводится в вёрстке
        inlines = [CardInline(self.model, self.admin_site)]
        if obj and obj.slug in PAGE_GALLERY_SLUGS:
            inlines.insert(0, PagePhotoInline(self.model, self.admin_site))
        return inlines

    def get_fieldsets(self, request, obj=None):
        fs = [
            ('Какая страница', {'fields': ('admin_title', 'product_slug', 'slug')}
             if obj is None or obj.product_slug else {'fields': ('admin_title', 'slug')}),
            ('Тексты', {'fields': ('h1', 'subtitle', 'body')}),
        ]
        slug = getattr(obj, 'slug', None)
        if obj is None or obj.product_slug or slug == 'produkciya_mineralnyy_poroshok':
            fs.append(('Фон шапки', {'description': 'Загрузите короткое MP4/WEBM для фонового видео. Фото показывается до загрузки видео и на телефонах.',
                                     'fields': ('video_file', 'photo', 'video_url')}))
        if slug in PAGE_PHOTO_HINT:
            fs.append(('Фото', {'description': PAGE_PHOTO_HINT[slug], 'fields': ('photo',)}))
        fs.append(('SEO — как страница выглядит в поиске', {
            'description': 'Если оставить пустым, поисковик увидит заголовок страницы.',
            'fields': ('seo_title', 'seo_description'),
        }))
        return fs

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return bool(obj and obj.product_slug)

    def get_readonly_fields(self, request, obj=None):
        return ('slug', 'admin_title') if obj and not obj.product_slug else (
            ('slug', 'product_slug') if obj else ('slug',))

    def save_model(self, request, obj, form, change):
        if not change:
            obj.slug = f'custom_produkciya_{obj.product_slug.replace("-", "_")}'
            if not obj.h1:
                obj.h1 = obj.admin_title
        super().save_model(request, obj, form, change)

    @admin.display(description='SEO заполнено', boolean=True)
    def has_seo(self, obj):
        return bool(obj.seo_title or obj.seo_description)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('title', 'page', 'section', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)
    list_filter = ('page', 'section', 'published')
    search_fields = ('title', 'text')
