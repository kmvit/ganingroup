# -*- coding: utf-8 -*-
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LeadForm, HaulerLeadForm, VacancyApplicationForm
from .notify import notify_application, notify_hauler, notify_lead
from .models import (ConcreteGrade, Department, Direction, Document, MapPoint, Page,
                     ProjectObject, Review, Stat, TeamMember, TimelineEvent, Vacancy)

# (url_path, url_name, шаблон, active-ключ для подсветки меню)
PAGES = [
    ('',                              'home',                         'index',                        ''),
    ('o-gruppe/',                     'o_gruppe',                     'o_gruppe',                     'o_gruppe'),
    ('resheniya/',                    'resheniya',                    'resheniya',                    'resheniya'),
    ('resheniya/zastroyshchikam/',    'reshenie_zastroyshchikam',     'reshenie_zastroyshchikam',     'resheniya'),
    ('resheniya/kommercheskoe/',      'reshenie_kommercheskoe',       'reshenie_kommercheskoe',       'resheniya'),
    ('resheniya/dorozhnikam/',        'reshenie_dorozhnikam',         'reshenie_dorozhnikam',         'resheniya'),
    ('resheniya/promyshlennost/',     'reshenie_promyshlennost',      'reshenie_promyshlennost',      'resheniya'),
    ('resheniya/chastnaya-zastroyka/','reshenie_chastnaya_zastroyka', 'reshenie_chastnaya_zastroyka', 'resheniya'),
    ('produkciya/',                   'produkciya',                   'produkciya',                   'produkciya'),
    ('produkciya/beton/',             'produkciya_beton',             'produkciya_beton',             'produkciya'),
    ('produkciya/zhbi/',              'produkciya_zhbi',              'produkciya_zhbi',              'produkciya'),
    ('produkciya/asfalt/',            'produkciya_asfalt',            'produkciya_asfalt',            'produkciya'),
    ('produkciya/inertnye/',          'produkciya_inertnye',          'produkciya_inertnye',          'produkciya'),
    ('produkciya/cement/',            'produkciya_cement',            'produkciya_cement',            'produkciya'),
    ('produkciya/beton-m350/',        'produkciya_kartochka',         'produkciya_kartochka',         'produkciya'),
    ('uslugi/',                       'uslugi',                       'uslugi',                       'uslugi'),
    ('uslugi/logistika/',             'logistika',                    'logistika',                    'uslugi'),
    ('uslugi/raschet-opalubki/',      'raschet_opalubki',             'raschet_opalubki',             'uslugi'),
    ('uslugi/shef-montazh/',          'shef_montazh',                 'shef_montazh',                 'uslugi'),
    ('uslugi/laboratoriya/',          'laboratoriya',                 'laboratoriya',                 'uslugi'),
    ('obekty/',                       'obekty',                       'obekty',                       'obekty'),
    ('obekty/zhk-nazvanie/',          'obekt',                        'obekt',                        'obekty'),
    ('kariera/',                      'kariera',                      'kariera',                      'kariera'),
    ('kontakty/',                     'kontakty',                     'kontakty',                     'kontakty'),
    ('kalkulyator/',                  'kalkulyator',                  'kalkulyator',                  'produkciya'),
    ('policy/',                       'policy',                       'policy',                       ''),
    ('consent/',                      'consent',                      'consent',                      ''),
    ('aidentika/',                    'aidentika',                    'aidentika',                    ''),
]


def page_extras(slug: str) -> dict:
    """Контентные наборы, нужные конкретным страницам."""
    if slug == 'home':
        return {
            'stats': Stat.objects.filter(published=True),
            'directions': Direction.objects.filter(published=True),
            'objects': ProjectObject.objects.filter(published=True, is_featured=True),
            'team': TeamMember.objects.filter(published=True, is_featured=True),
            'review': Review.objects.filter(published=True, is_featured=True).first(),
            'map_points': MapPoint.objects.filter(published=True),
        }
    if slug == 'o_gruppe':
        return {
            'stats': Stat.objects.filter(published=True),
            'timeline': TimelineEvent.objects.filter(published=True),
            'documents': Document.objects.filter(published=True),
            'team': TeamMember.objects.filter(published=True),
        }
    if slug == 'obekty':
        return {'objects': ProjectObject.objects.filter(published=True)}
    if slug == 'kontakty':
        return {'departments': Department.objects.filter(published=True),
                'map_points': MapPoint.objects.filter(published=True)}
    if slug == 'kariera':
        return {'vacancies': Vacancy.objects.filter(published=True)}
    if slug == 'produkciya':
        return {'directions': Direction.objects.filter(published=True)}
    if slug in ('kalkulyator', 'produkciya_beton'):
        return {'grades': ConcreteGrade.objects.filter(published=True)}
    return {}


def make_page_view(template: str, active: str, slug: str):
    """Фабрика страниц: шаблон, активный пункт меню, тексты и контент из БД."""
    def view(request):
        page = Page.objects.filter(slug=slug).first()
        cards = list(page.cards.filter(published=True)) if page else []
        by_section = {}
        for c in cards:
            by_section.setdefault(c.section, []).append(c)
        ctx = {
            'active': active,
            'page': page,
            'cards': cards,
            'cards_by_section': by_section,
            'lead_form': LeadForm(),
        }
        ctx.update(page_extras(slug))
        return render(request, f'pages/{template}.html', ctx)
    view.__name__ = f'page_{template}'
    return view


def _back(request, fragment: str):
    """Вернуться на страницу, с которой отправляли форму."""
    target = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    target = target.split('#')[0]
    return HttpResponseRedirect(f'{target}{fragment}')


@require_POST
def lead_create(request):
    """Приём заявки «Запросить ТКП» (модальная форма на всех страницах)."""
    form = LeadForm(request.POST)
    if form.is_valid():
        lead = form.save(commit=False)
        lead.page = (request.POST.get('next') or '')[:200]
        lead.save()
        notify_lead(lead)
        return _back(request, '#tkp-ok')
    for errors in form.errors.values():
        for err in errors:
            messages.error(request, err)
    return _back(request, '#tkp')


@require_POST
def hauler_create(request):
    """Приём заявки перевозчика (блок #haulers на «Карьере»)."""
    form = HaulerLeadForm(request.POST)
    if form.is_valid():
        notify_hauler(form.save())
        return _back(request, '#tkp-ok')
    for errors in form.errors.values():
        for err in errors:
            messages.error(request, err)
    return _back(request, '#haulers')


@require_POST
def application_create(request):
    """Приём отклика на вакансию (с резюме) — блок #vac на «Карьере»."""
    form = VacancyApplicationForm(request.POST, request.FILES)
    if form.is_valid():
        notify_application(form.save())
        return _back(request, '#tkp-ok')
    for errors in form.errors.values():
        for err in errors:
            messages.error(request, err)
    return _back(request, '#vac')


def page_not_found(request, exception=None):
    """Кастомная 404 (шаблон уже свёрстан)."""
    return render(request, 'pages/404.html', {'active': ''}, status=404)
