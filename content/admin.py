# -*- coding: utf-8 -*-
"""Админка: содержание сайта."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (CatalogItem, Department, Direction, Document, MapPoint,
                     ObjectPhoto, ObjectStat, ProjectObject, Review, Stat,
                     TeamMember, TimelineEvent, Vacancy)


def photo_preview(obj, field='photo', height=44):
    f = getattr(obj, field, None)
    if not f:
        return '—'
    return format_html('<img src="{}" style="height:{}px;border:1px solid #ddd" />', f.url, height)


class PhotoMixin:
    @admin.display(description='Фото')
    def preview(self, obj):
        return photo_preview(obj)


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


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'section', 'chips', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)
    list_filter = ('section', 'published')
    search_fields = ('title', 'chips')


class ObjectStatInline(admin.TabularInline):
    model = ObjectStat
    extra = 0
    fields = ('value', 'sup', 'label', 'note', 'order', 'published')


class ObjectPhotoInline(admin.TabularInline):
    model = ObjectPhoto
    extra = 0
    fields = ('image', 'caption', 'order', 'published')


@admin.register(ProjectObject)
class ProjectObjectAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'city', 'direction', 'is_featured', 'order', 'published')
    list_editable = ('is_featured', 'order', 'published')
    list_display_links = ('title',)
    list_filter = ('is_featured', 'published', 'direction')
    search_fields = ('title', 'city', 'summary')
    inlines = [ObjectStatInline, ObjectPhotoInline]
    fieldsets = (
        (None, {'fields': ('title', 'summary', 'photo')}),
        ('Данные объекта', {'fields': ('city', 'direction', 'year', 'volume')}),
        ('Страница кейса', {
            'description': 'Заголовок и блок «Как это было». Пустые поля на странице '
                           'не показываются. Цифры-плашки и фото-галерея — ниже.',
            'fields': ('headline', 'context', 'challenge', 'solution', 'result'),
        }),
        ('Отзыв по объекту (необязательно)', {
            'fields': ('quote_text', 'quote_author', 'quote_role'),
        }),
        ('Показ', {'fields': ('is_featured', 'order', 'published', 'slug')}),
    )
    readonly_fields = ('slug',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin, PhotoMixin):
    list_display = ('title', 'preview', 'person', 'phone', 'email', 'order', 'published')
    list_editable = ('order', 'published')
    list_display_links = ('title',)


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


@admin.register(MapPoint)
class MapPointAdmin(admin.ModelAdmin):
    list_display = ('title', 'lat', 'lng', 'is_own', 'order', 'published')
    list_editable = ('lat', 'lng', 'is_own', 'order', 'published')
    list_display_links = ('title',)
    fieldsets = (
        (None, {'fields': ('title', 'is_own')}),
        ('Координаты (для Яндекс.Карты)', {'fields': ('lat', 'lng')}),
        ('Схематичная карта без ключа', {
            'classes': ('collapse',),
            'fields': ('left', 'top'),
        }),
        ('Показ', {'fields': ('order', 'published')}),
    )
