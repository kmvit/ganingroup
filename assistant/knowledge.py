"""Small, auditable index of the two public sites."""
import re
from collections import Counter, deque
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from django.utils import timezone
from django.urls import reverse
from django.utils.html import strip_tags

from calc.models import ConcreteGrade, DeliveryZone
from content.models import CatalogItem, Department, Direction, Document, ProjectObject, TeamMember, Vacancy
from content.utils import SD2_URLS

from .models import KnowledgePage

ROOTS = {'ganin': 'https://ganin-group.ru/', 'sd2': 'https://sd2-kmv.ru/'}
PRODUCT_SECTIONS = {
    'concrete': 'produkciya_beton', 'precast': 'produkciya_zhbi',
    'asphalt': 'produkciya_asfalt', 'aggregates': 'produkciya_inertnye',
}
GANIN_PRODUCT_ROUTES = {
    'cement': ('produkciya_cement',),
    'mineral_powder': ('produkciya_mineralnyy_poroshok',),
    'formwork': ('raschet_opalubki', 'shef_montazh'),
}
SKIP_PREFIXES = ('/admin/', '/zayavka/', '/assistant/', '/static/', '/media/')
WORDS = re.compile(r'[а-яёa-z0-9]{3,}', re.I)
STOP_WORDS = {'какие', 'какую', 'какой', 'какая', 'какое', 'каких', 'каком', 'кто', 'когда',
              'почему', 'зачем', 'сколько', 'есть', 'ли', 'где', 'куда', 'как', 'что', 'она',
              'они', 'для', 'или', 'можно', 'либо', 'вас', 'ваши', 'ваших',
              'ганин', 'групп', 'стройдеталь', 'завод', 'сайт', 'сайте'}
ALIASES = {'ваканс': ('работ', 'карьер', 'позиц'),
           'размер': ('типора', 'длина', 'ширин', 'высот'),
           'позвон': ('контак', 'телефо'),
           'менедж': ('контак', 'телефо'),
           'наход': ('адрес', 'контак'),
           'стоит': ('цен', 'стоимо'),
           'возите': ('достав', 'логист'), 'везете': ('достав', 'логист'),
           'везёте': ('достав', 'логист'), 'привез': ('достав', 'логист'),
           'достав': ('логист',)}


def project_url(slug):
    return urljoin(ROOTS['ganin'], reverse('obekt', args=[slug]))


def team_knowledge():
    """Public staff and department contacts shared by both brands."""
    entries = [{
        'site': 'ganin', 'title': member.name,
        'url': urljoin(ROOTS['ganin'], reverse('o_gruppe')) + '#komanda',
        'excerpt': f'Общая команда ГАНИН ГРУПП и Стройдеталь-2. {member.name}. {member.position}',
    } for member in TeamMember.objects.filter(published=True)]
    for department in Department.objects.filter(published=True):
        details = [department.title, department.person, department.position]
        if department.phone:
            details.append(f'Телефон: {department.phone}')
        if department.email:
            details.append(f'Электронная почта: {department.email}')
        entries.append({
            'site': 'ganin', 'title': department.title,
            'url': urljoin(ROOTS['ganin'], reverse('kontakty')),
            'excerpt': 'Общие отделы и контакты ГАНИН ГРУПП и Стройдеталь-2. '
                       + '. '.join(detail for detail in details if detail),
        })
    contact_urls = [urljoin(root, 'kontakty') + suffix
                    for root in ROOTS.values() for suffix in ('', '/')]
    pages = KnowledgePage.objects.filter(
        url__in=contact_urls, fetched_at__gte=timezone.now() - timedelta(days=7))
    entries.extend(_indexed_entry(page) for page in pages)
    return entries


def delivery_knowledge():
    zones = list(DeliveryZone.objects.filter(published=True).values_list('title', flat=True))
    return [{
        'site': 'ganin', 'title': 'Зоны доставки бетона',
        'url': urljoin(ROOTS['ganin'], reverse('logistika')),
        'excerpt': ('Населённые пункты из справочника доставки бетона:\n'
                    + ('\n'.join(zones) or 'Зоны не указаны.')
                    + '\nДля остальных населённых пунктов условия уточняются отдельно.'),
    }]


def project_knowledge():
    objects = list(ProjectObject.objects.filter(published=True).values('title', 'slug', 'city', 'summary'))
    cities = Counter(obj['city'].strip() for obj in objects if obj['city'].strip())
    city_counts = ', '.join(f'{city} — {count}' for city, count in cities.most_common()) or 'города не указаны'
    return [
        {
            'site': 'ganin', 'title': 'Итоги по опубликованным объектам',
            'url': '',
            'excerpt': (f'Всего опубликовано карточек: {len(objects)}. По указанным городам: {city_counts}. '
                        f'Без указания города: {len(objects) - sum(cities.values())}. '
                        'Карточки без города входят в общий список. '
                        'Отдельного статуса завершения строительства в каталоге нет.'),
        },
        *[
            {'site': 'ganin', 'title': obj['title'], 'url': project_url(obj['slug']),
             'excerpt': f'Город: {obj["city"].strip() or "не указан"}. {obj["summary"]}'}
            for obj in objects
        ],
    ]


def product_directions(formwork_only=False):
    directions = Direction.objects.filter(published=True).select_related('page')
    if formwork_only:
        directions = directions.filter(is_upex=True)
    entries = []
    for row in directions:
        href = row.href
        if row.is_upex or row.url_name in SD2_URLS or href.startswith('/produkciya/'):
            entries.append({'site': 'ganin', 'title': row.title,
                            'url': urljoin(ROOTS['ganin'], href) if href else '',
                            'excerpt': row.tagline if formwork_only else
                                       'Направление продукции. Характеристики и цены — в подробном каталоге.'})
    return entries


def product_reference(section):
    section_title = dict(CatalogItem.SECTIONS)[section]
    rows = CatalogItem.objects.filter(published=True, section=section).values_list('title', 'chips')
    lines = [f'{title} — {chips}' if chips else title for title, chips in rows]
    if section == PRODUCT_SECTIONS['concrete']:
        grades = ConcreteGrade.objects.filter(published=True).values_list('title', 'grade_class', 'note')
        lines.extend(' · '.join(filter(None, row)) for row in grades)
    if not lines:
        return []
    return [{
        'site': 'ganin', 'title': f'Справочные позиции ГАНИН — {section_title}', 'url': SD2_URLS[section],
        'excerpt': ('Позиции локального справочника. Текущий ассортимент и характеристики сверяй '
                    'с опубликованным каталогом СД2. Доступность и цены этот справочник не подтверждает.\n'
                    + '\n'.join(lines)),
    }]


def product_knowledge(site, category, query=''):
    if category == 'overview' and site == 'ganin':
        return product_directions()
    if category in GANIN_PRODUCT_ROUTES:
        if site != 'ganin':
            return []
        urls = [urljoin(ROOTS[site], reverse(route)) for route in GANIN_PRODUCT_ROUTES[category]]
        entries = product_directions(formwork_only=True) if category == 'formwork' else []
        entries.extend(_indexed_entry(page) for page in KnowledgePage.objects.filter(
            site=site, url__in=urls, fetched_at__gte=timezone.now() - timedelta(days=7)))
        return entries
    sections = PRODUCT_SECTIONS.values() if category == 'overview' else [PRODUCT_SECTIONS[category]]
    pages = KnowledgePage.objects.filter(site='sd2', fetched_at__gte=timezone.now() - timedelta(days=7))
    urls = [SD2_URLS[section] for section in sections]
    main_pages = pages.filter(url__in=[variant for url in urls for variant in (url, url + '/')])
    entries = [
        {'site': 'sd2', 'title': page.title, 'url': page.url,
         'excerpt': page.content if category != 'overview' else 'Раздел каталога СД2'}
        for page in main_pages
    ]
    if category == 'precast':
        details = list(pages.filter(url__startswith=ROOTS['sd2'] + 'zhelezobeton/'))
        terms = _terms(query)
        matching = sorted((page for page in details if terms & _terms(page.title)),
                          key=lambda page: len(terms & _terms(page.title)), reverse=True)
        if matching:
            entries = [_indexed_entry(page) for page in matching[:3]] + entries
        else:
            entries.extend(_indexed_entry(page, 'Карточка изделия ЖБИ') for page in details)
    if not entries and site == 'ganin':
        entries.extend(product_reference(PRODUCT_SECTIONS[category]))
    return entries


def _indexed_entry(page, excerpt=None):
    return {'site': page.site, 'title': page.title, 'url': page.url,
            'excerpt': page.content if excerpt is None else excerpt}


def document_knowledge():
    entries = []
    for document in Document.objects.filter(published=True):
        link = urljoin(ROOTS['ganin'], document.file.url) if document.file else ''
        entries.append({
            'site': 'ganin', 'title': document.title, 'url': link,
            'excerpt': ' · '.join(filter(None, (document.kind, strip_tags(document.summary))))
                       or 'Опубликованный документ ГАНИН ГРУПП.',
        })
    return entries


def vacancy_knowledge():
    url = urljoin(ROOTS['ganin'], reverse('kariera'))
    return [
        {'site': 'ganin', 'title': row.title, 'url': url,
         'excerpt': ' · '.join(strip_tags(value) for value in
                               (row.kind, row.salary, row.summary, row.description) if value)}
        for row in Vacancy.objects.filter(published=True)
    ] or [{'site': 'ganin', 'title': 'Вакансии ГАНИН ГРУПП', 'url': url,
           'excerpt': 'Сейчас на сайте нет опубликованных вакансий.'}]


def _key(word):
    if word.startswith('автобетононасос'):
        word = word[4:]
    if word.startswith('цен') and len(word) >= 4:
        return 'цен'
    return word[:6] if len(word) > 6 else word[:5] if len(word) > 5 else word


def _terms(text, expand=False):
    result = {_key(word) for word in WORDS.findall(text.lower())
              if word not in STOP_WORDS}
    if expand:
        for key, aliases in ALIASES.items():
            if key in result:
                result.update(aliases)
    return result


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_title = False
        self.in_row = False
        self.in_cell = False
        self.title = []
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'form', 'noscript'):
            self.skip += 1
        if tag == 'title':
            self.in_title = True
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'tr':
            self.in_row = True
        if tag in ('td', 'th'):
            self.in_cell = True
        if tag == 'br' and self.in_cell:
            self.text.append(' / ')
        elif tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr', 'section', 'article', 'br'):
            self.text.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'form', 'noscript'):
            self.skip = max(0, self.skip - 1)
        if tag == 'title':
            self.in_title = False
        if tag == 'tr':
            self.in_row = False
        if tag in ('td', 'th'):
            self.in_cell = False
            if not self.skip:
                self.text.append(' | ')

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.skip:
            if not self.in_row:
                self.text.append(data)
            elif self.in_cell:
                self.text.append(re.sub(r'\s+', ' ', data))


def normalized_url(base, href, host):
    url = urldefrag(urljoin(base, href))[0]
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in (host, f'www.{host}'):
        return None
    if parsed.query or parsed.path.startswith(SKIP_PREFIXES):
        return None
    if re.search(r'\.(?:pdf|jpe?g|png|webp|svg|mp4|zip|xml|css|js)$', parsed.path, re.I):
        return None
    return f'https://{host}{parsed.path or "/"}'


def fetch_page(url):
    req = Request(url, headers={'User-Agent': 'GaninAssistantIndexer/1.0 (+https://ganin-group.ru/)'})
    with urlopen(req, timeout=15) as response:
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return None
        raw = response.read(600_001)
        if len(raw) > 600_000:
            return None
        charset = response.headers.get_content_charset() or 'utf-8'
    parser = PageParser()
    parser.feed(raw.decode(charset, errors='replace'))
    title = re.sub(r'\s+', ' ', ''.join(parser.title)).strip()[:250]
    content = re.sub(r'[ \t]+', ' ', ''.join(parser.text))
    content = re.sub(r'\n\s*\n+', '\n', content).strip()
    return title, content[:60_000], parser.links


def refresh_site(site, limit=150):
    root = ROOTS[site]
    host = urlparse(root).hostname
    queue = deque([root])
    seen = set()
    saved = 0
    while queue and len(seen) < limit:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            result = fetch_page(url)
        except Exception:  # An unavailable page must not erase the previous index.
            continue
        if not result:
            continue
        title, content, links = result
        if title and len(content) >= 80:
            KnowledgePage.objects.update_or_create(
                url=url, defaults={'site': site, 'title': title, 'content': content})
            saved += 1
        for href in links:
            target = normalized_url(url, href, host)
            if target and target not in seen and target not in queue:
                queue.append(target)
    return saved


def search_pages(question, limit=3, site=None):
    terms = _terms(question, expand=True)
    if not terms:
        return []
    ranked = []
    career_query = bool(re.search(r'ваканс|работат|трудоустр|резюме|сотрудник|персонал|должност|работ[ауе]\s+в\s+', question, re.I))
    privacy_query = bool(re.search(r'политик|соглас|персональ|cookie|куки|данны|конфиденц', question, re.I))
    pages = KnowledgePage.objects.filter(fetched_at__gte=timezone.now() - timedelta(days=7))
    if site:
        pages = pages.filter(site=site)
    for page in pages.iterator():
        if page.url.endswith('/kariera/') and not career_query:
            continue
        if page.url.rstrip('/').endswith(('/policy', '/consent', '/politika', '/soglasie')) and not privacy_query:
            continue
        title_terms = terms & _terms(page.title)
        paragraphs = [p.strip() for p in page.content.split('\n') if len(p.strip()) > 25]
        for index, paragraph in enumerate(paragraphs):
            if paragraph == page.title:
                continue
            paragraph_terms = terms & _terms(paragraph)
            if not paragraph_terms and not title_terms:
                continue
            score = len(paragraph_terms | title_terms) * 8 + len(paragraph_terms) * 3 + len(title_terms)
            # Nearby lines often carry the answer under a short heading or label.
            start = page.content.find(paragraphs[max(0, index - 1)])
            excerpt = page.content[start:start + 1500] if start >= 0 else paragraph[:1500]
            ranked.append((score, page, excerpt))
    ranked.sort(key=lambda row: row[0], reverse=True)
    chosen = []
    seen = set()
    for score, page, excerpt in ranked:
        if page.url in seen:
            continue
        chosen.append({'site': page.site, 'title': page.title, 'url': page.url, 'excerpt': excerpt})
        seen.add(page.url)
        if len(chosen) >= limit:
            break
    return chosen
