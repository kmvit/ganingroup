# -*- coding: utf-8 -*-
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LeadForm, HaulerLeadForm, VacancyApplicationForm
from .notify import notify_application, notify_hauler, notify_lead
from calc.models import ConcreteGrade, ConstructionType, DeliveryZone
from content.models import (CatalogItem, Department, Direction, Document, MapPoint,
                            ProjectObject, Review, Stat, TeamMember, TimelineEvent, Vacancy)
from core.models import Page

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
            'assets': Direction.objects.filter(published=True, show_in_assets=True),
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
        extras = {'grades': ConcreteGrade.objects.filter(published=True),
                  'zones': DeliveryZone.objects.filter(published=True),
                  'ctypes': ConstructionType.objects.filter(published=True)}
        if slug == 'produkciya_beton':
            extras['catalog'] = CatalogItem.objects.filter(published=True, section=slug)
        return extras
    if slug in ('produkciya_zhbi', 'produkciya_asfalt', 'produkciya_inertnye'):
        return {'catalog': CatalogItem.objects.filter(published=True, section=slug)}
    if slug.startswith('reshenie_'):
        # плитки «Продукция под сегмент» берут фото из направлений (по маршруту),
        # чтобы не грузить фото на каждую страницу решения отдельно
        dirs = list(Direction.objects.filter(published=True))
        ctx = {'dir_by_url': {d.url_name: d for d in dirs if d.url_name},
               'upex_dir': next((d for d in dirs if d.is_upex), None)}
        # кейсы на страницах решений — реальные объекты из БД («Объекты»)
        seg = {'reshenie_zastroyshchikam': dict(direction='бетон'),
               'reshenie_promyshlennost': dict(direction='опалубка')}
        if slug == 'reshenie_kommercheskoe':
            ctx['objects'] = ProjectObject.objects.filter(published=True)
        elif slug in seg:
            ctx['objects'] = ProjectObject.objects.filter(published=True, **seg[slug])
        return ctx
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


# служебные страницы не отдаём поисковикам
SITEMAP_EXCLUDE = {'policy', 'consent', 'aidentika'}


def sitemap_xml(request):
    base = f'{request.scheme}://{request.get_host()}'
    locs = [p for p, name, _tpl, _active in PAGES if name not in SITEMAP_EXCLUDE]
    locs += [f'obekty/{o.slug}/'
             for o in ProjectObject.objects.filter(published=True)]
    items = ''.join(f'  <url><loc>{base}/{loc}</loc></url>\n' for loc in locs)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f'{items}</urlset>\n')
    return HttpResponse(xml, content_type='application/xml')


def robots_txt(request):
    base = f'{request.scheme}://{request.get_host()}'
    text = ('User-agent: *\n'
            'Disallow: /admin/\n'
            'Disallow: /zayavka/\n'
            'Disallow: /policy/\n'
            'Disallow: /consent/\n'
            'Disallow: /aidentika/\n'
            f'Sitemap: {base}/sitemap.xml\n')
    return HttpResponse(text, content_type='text/plain')


def object_detail(request, slug):
    """Страница кейса конкретного объекта (obekty/<slug>/)."""
    obj = get_object_or_404(ProjectObject, slug=slug, published=True)
    headline = obj.headline or obj.title
    # page-подобный словарь только ради SEO и дефолтов в base.html
    page = {
        'seo_title': f'{obj.title}, {obj.city} — кейс | ГАНИН ГРУПП'
                     if obj.city else f'{obj.title} — кейс | ГАНИН ГРУПП',
        'seo_description': obj.summary,
        'title_tag': obj.title,
        'h1': headline,
        'subtitle': obj.summary,
    }
    return render(request, 'pages/obekt.html', {
        'active': 'obekty', 'page': page, 'object': obj, 'headline': headline,
    })


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
