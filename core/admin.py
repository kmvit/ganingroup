# -*- coding: utf-8 -*-
"""Админка: общие данные, меню и страницы."""
from django.contrib import admin
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
    fields = ('title', 'url_name', 'external_url', 'order', 'published')
    verbose_name = 'Подпункт'
    verbose_name_plural = 'Подпункты меню'


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
        ('Куда ведёт', {'fields': ('url_name', 'external_url')}),
        ('Показ', {'fields': ('footer_title', 'show_in_footer', 'order', 'published')}),
    )

    def get_queryset(self, request):
        # в списке показываем разделы верхнего уровня и подпункты вместе, но сортировкой по дереву
        return super().get_queryset(request).select_related('parent')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('admin_title', 'h1', 'slug', 'has_seo')
    search_fields = ('admin_title', 'h1', 'subtitle', 'body')
    readonly_fields = ('slug', 'admin_title')
    inlines = [PagePhotoInline, CardInline]
    fieldsets = (
        ('Какая страница', {'fields': ('admin_title', 'slug')}),
        ('Тексты', {'fields': ('h1', 'subtitle', 'body')}),
        ('Фото', {
            'description': 'Главное фото страницы: фон шапки у решений и кейса, '
                           'фото слева у сервисов, главное фото товара на карточке. '
                           'Галерея (фото кейса, галерея товара) — внизу страницы.',
            'fields': ('photo',),
        }),
        ('SEO — как страница выглядит в поиске', {
            'description': 'Если оставить пустым, поисковик увидит заголовок страницы.',
            'fields': ('seo_title', 'seo_description'),
        }),
    )

    def has_add_permission(self, request):
        return False        # набор страниц задан вёрсткой

    def has_delete_permission(self, request, obj=None):
        return False

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
