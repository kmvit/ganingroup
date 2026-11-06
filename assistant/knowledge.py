"""Small, auditable index of the two public sites."""
import re
from collections import deque
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from django.utils import timezone

from .models import KnowledgePage

ROOTS = {'ganin': 'https://ganin-group.ru/', 'sd2': 'https://sd2-kmv.ru/'}
SKIP_PREFIXES = ('/admin/', '/zayavka/', '/assistant/', '/static/', '/media/')
WORDS = re.compile(r'[а-яёa-z0-9]{3,}', re.I)
STOP_WORDS = {'какие', 'какую', 'какой', 'сколько', 'есть', 'ли', 'где', 'как', 'что', 'она',
              'они', 'для', 'или', 'можно', 'либо', 'вас', 'ваши', 'ваших',
              'ганин', 'групп', 'стройдеталь', 'завод', 'сайт', 'сайте'}
ALIASES = {'ваканс': ('работ', 'карьер', 'позиц'),
           'размер': ('типора', 'длина', 'ширин', 'высот'),
           'позвон': ('контак', 'телефо'),
           'менедж': ('контак', 'телефо'),
           'наход': ('адрес', 'контак'),
           'стоит': ('цен', 'стоимо')}


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
    pages = KnowledgePage.objects.filter(fetched_at__gte=timezone.now() - timedelta(days=7))
    if site:
        pages = pages.filter(site=site)
    for page in pages.iterator():
        title_hits = len(terms & _terms(page.title))
        paragraphs = [p.strip() for p in page.content.split('\n') if len(p.strip()) > 25]
        for index, paragraph in enumerate(paragraphs):
            if paragraph == page.title:
                continue
            paragraph_hits = len(terms & _terms(paragraph))
            if not paragraph_hits and not title_hits:
                continue
            score = paragraph_hits * 3 + title_hits * 8
            start = 0 if title_hits >= 2 else page.content.find(paragraph)
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
