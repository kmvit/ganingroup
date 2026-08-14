# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html

from .models import (Card, Department, Direction, Document, HaulerLead, Lead, MapPoint,
                     MenuItem, Page, ProjectObject, Review, SiteSettings, Stat, TeamMember,
                     TimelineEvent, Vacancy, VacancyApplication)

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


# ============================================================ ЗАЯВКИ

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'company', 'created', 'processed')
    list_filter = ('processed', 'created')
    search_fields = ('name', 'phone', 'company', 'details')
    list_editable = ('processed',)
    readonly_fields = ('created', 'page')

    def has_add_permission(self, request):
        return False        # заявки приходят с сайта, вручную не добавляют


@admin.register(HaulerLead)
class HaulerLeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'vehicles', 'created', 'processed')
    list_filter = ('processed', 'created')
    search_fields = ('name', 'phone', 'vehicles')
    list_editable = ('processed',)
    readonly_fields = ('created',)

    def has_add_permission(self, request):
        return False


@admin.register(VacancyApplication)
class VacancyApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'target', 'resume', 'created', 'processed')
    list_filter = ('processed', 'created', 'vacancy')
    search_fields = ('name', 'phone', 'vacancy_title', 'comment')
    list_editable = ('processed',)
    readonly_fields = ('created',)

    def has_add_permission(self, request):
        return False

    @admin.display(description='Вакансия')
    def target(self, obj):
        return obj.vacancy or obj.vacancy_title or '—'


# ============================================================ ОБЩИЕ ДАННЫЕ

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Одна запись на весь сайт — добавлять и удалять нельзя, только править."""

    fieldsets = (
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
            'fields': ('slogan', 'founded_year', 'legal_name', 'copyright_note', 'footer_about'),
        }),
        ('Внешние ссылки', {'fields': ('upex_url', 'messenger_url')}),
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


# ============================================================ КОНТЕНТ ГЛАВНОЙ

@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('value', 'sup', 'label', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('value',)


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'tagline', 'size', 'is_upex', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)
    fieldsets = (
        (None, {'fields': ('title', 'tagline', 'photo')}),
        ('Ссылка', {'fields': ('url_name', 'external_url')}),
        ('Вид плитки', {'fields': ('size', 'is_upex')}),
        ('Показ', {'fields': ('order', 'published')}),
    )


@admin.register(ProjectObject)
class ProjectObjectAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'city', 'direction', 'is_featured', 'order', 'published')
    list_editable = ('is_featured', 'order', 'published')
    list_display_links = ('title',)
    list_filter = ('is_featured', 'published', 'direction')
    search_fields = ('title', 'city', 'summary')
    prepopulated_fields = {}
    fieldsets = (
        (None, {'fields': ('title', 'summary', 'photo')}),
        ('Данные объекта', {'fields': ('city', 'direction', 'year', 'volume')}),
        ('Показ', {'fields': ('is_featured', 'order', 'published', 'slug')}),
    )
    readonly_fields = ('slug',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('name', 'preview', 'position', 'is_featured', 'order', 'published')
    list_editable = ('is_featured', 'order', 'published')
    list_display_links = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('author', 'author_role', 'short', 'is_featured', 'order', 'published')
    list_editable = ('is_featured', 'order', 'published')
    list_display_links = ('author',)

    @admin.display(description='Отзыв')
    def short(self, obj):
        return obj.text[:60] + ('…' if len(obj.text) > 60 else '')


@admin.register(MapPoint)
class MapPointAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_own', 'left', 'top', 'order', 'published')
    list_editable = ('is_own', 'left', 'top', 'order', 'published')
    list_display_links = ('title',)


# ============================================================ РАЗДЕЛЫ

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'person', 'phone', 'email', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'salary', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)
    list_filter = ('kind', 'published')
    search_fields = ('title', 'summary', 'description')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'file', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('year',)


# ============================================================ СТРАНИЦЫ

class CardInline(admin.TabularInline):
    """Плитки правятся прямо внутри своей страницы."""
    model = Card
    extra = 0
    fields = ('section', 'icon', 'title', 'text', 'url_name', 'link_label', 'order', 'published')
    ordering = ('section', 'order')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('admin_title', 'h1', 'slug', 'has_seo')
    search_fields = ('admin_title', 'h1', 'subtitle', 'body')
    readonly_fields = ('slug', 'admin_title')
    inlines = [CardInline]
    fieldsets = (
        ('Какая страница', {'fields': ('admin_title', 'slug')}),
        ('Тексты', {'fields': ('h1', 'subtitle', 'body')}),
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


# ============================================================ МЕНЮ

class MenuChildInline(admin.TabularInline):
    """Подпункты правятся внутри своего раздела."""
    model = MenuItem
    fk_name = 'parent'
    extra = 0
    fields = ('title', 'url_name', 'external_url', 'order', 'published')
    verbose_name = 'Подпункт'
    verbose_name_plural = 'Подпункты меню'


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
