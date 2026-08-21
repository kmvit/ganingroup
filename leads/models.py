# -*- coding: utf-8 -*-
"""Заявки с сайта: ТКП, перевозчики, отклики на вакансии."""
from django.db import models


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
        db_table = 'pages_lead'
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
        db_table = 'pages_haulerlead'
        verbose_name = 'Заявка перевозчика'
        verbose_name_plural = 'Заявки перевозчиков'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} · {self.phone}'


class VacancyApplication(models.Model):
    """Отклик на вакансию с резюме (страница «Карьера»)."""

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=40)
    vacancy = models.ForeignKey('content.Vacancy', verbose_name='Вакансия', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='applications')
    vacancy_title = models.CharField('Должность (текстом)', max_length=200, blank=True,
                                     help_text='Если вакансия выбрана не из списка')
    resume = models.FileField('Резюме', upload_to='resume/%Y-%m/', blank=True)
    comment = models.TextField('Комментарий', blank=True)
    created = models.DateTimeField('Получен', auto_now_add=True)
    processed = models.BooleanField('Обработан', default=False)

    class Meta:
        db_table = 'pages_vacancyapplication'
        verbose_name = 'Отклик на вакансию'
        verbose_name_plural = 'Отклики на вакансии'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} · {self.vacancy or self.vacancy_title or "без вакансии"}'
