"""Small, auditable index of the two public sites."""
import re
from collections import Counter, deque
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from django.utils import timezone
from django.urls import reverse

from calc.models import DeliveryZone
from content.models import ProjectObject

from .models import KnowledgePage

ROOTS = {'ganin': 'https://ganin-group.ru/', 'sd2': 'https://sd2-kmv.ru/'}
FULL_CONTEXT_CHAR_LIMIT = 150_000
SKIP_PREFIXES = ('/admin/', '/zayavka/', '/assistant/', '/static/', '/media/')
WORDS = re.compile(r'[а-яёa-z0-9]{3,}', re.I)
STOP_WORDS = {'какие', 'какую', 'какой', 'сколько', 'есть', 'ли', 'где', 'куда', 'как', 'что', 'она',
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


def structured_knowledge(site):
    """Give the model complete public datasets that fit alongside the page excerpts."""
    if site != 'ganin':
        return []
    zones = list(DeliveryZone.objects.filter(published=True).values_list('title', flat=True))
    objects = list(ProjectObject.objects.filter(published=True).values('title', 'slug', 'city', 'summary'))
    cities = Counter(obj['city'].strip() for obj in objects if obj['city'].strip())
    city_counts = ', '.join(f'{city} — {count}' for city, count in cities.most_common()) or 'города не указаны'
    return [
        {
            'site': site, 'title': 'Зоны доставки бетона',
            'url': urljoin(ROOTS[site], reverse('logistika')),
            'excerpt': ('Населённые пункты из справочника доставки бетона:\n'
                        + ('\n'.join(zones) or 'Зоны не указаны.')
                        + '\nДля остальных населённых пунктов условия уточняются отдельно.'),
        },
        {
            'site': site, 'title': 'Итоги по опубликованным объектам',
            'url': '',
            'excerpt': (f'Всего опубликовано карточек: {len(objects)}. По указанным городам: {city_counts}. '
                        f'Без указания города: {len(objects) - sum(cities.values())}. '
                        'Карточки без города входят в общий список. '
                        'Отдельного статуса завершения строительства в каталоге нет.'),
        },
        *[
            {'site': site, 'title': obj['title'], 'url': project_url(obj['slug']),
             'excerpt': f'Город: {obj["city"].strip() or "не указан"}. {obj["summary"]}'}
            for obj in objects
        ],
    ]


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


def matches_knowledge(question, entries):
    terms = _terms(question, expand=True)
    return any(terms & _terms(f'{entry["title"]} {entry["excerpt"]}') for entry in entries)


def site_knowledge(question, site):
    """Use the whole public index while it fits the request budget."""
    public_data = structured_knowledge(site)
    pages = [
        {'site': site, 'title': page.title, 'url': page.url, 'excerpt': page.content}
        for page in KnowledgePage.objects.filter(
            site=site, fetched_at__gte=timezone.now() - timedelta(days=7)).order_by('url')
    ]
    entries = public_data + pages
    if sum(len(entry['excerpt']) + len(entry['title']) + len(entry['url'])
           for entry in entries) > FULL_CONTEXT_CHAR_LIMIT:
        entries = public_data + search_pages(question, site=site)
    return entries if matches_knowledge(question, entries) else []


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_title = False
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
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr', 'section', 'article', 'br'):
            self.text.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'form', 'noscript'):
            self.skip = max(0, self.skip - 1)
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.skip:
            self.text.append(data)


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
