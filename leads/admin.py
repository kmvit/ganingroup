# -*- coding: utf-8 -*-
"""Админка: заявки с сайта."""
from django.contrib import admin

from .models import HaulerLead, Lead, VacancyApplication


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
