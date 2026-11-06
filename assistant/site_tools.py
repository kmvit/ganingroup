"""Read-only site data available to the assistant model."""
import json

from .knowledge import (
    GANIN_PRODUCT_ROUTES, PRODUCT_SECTIONS, delivery_knowledge, document_knowledge, product_knowledge,
    project_knowledge, search_pages, vacancy_knowledge,
)

MAX_RESULT_CHARS = 16_000


def _function(name, description, properties, required):
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
            'parameters': {
                'type': 'object',
                'properties': properties,
                'required': required,
                'additionalProperties': False,
            },
        },
    }


SEARCH = _function(
    'search_public_pages',
    'Поиск по публичным страницам текущего сайта: продукция, услуги, цены, контакты и другие разделы.',
    {'query': {'type': 'string', 'description': 'Ключевые слова для поиска на русском, до 240 символов.'}},
    ['query'],
)
DATASETS = {
    'projects': project_knowledge, 'delivery': delivery_knowledge,
    'documents': document_knowledge, 'vacancies': vacancy_knowledge,
}
CATALOG = _function(
    'read_public_catalog',
    'Актуальный справочник ГАНИН ГРУПП. projects — количество объектов, разбивка по городам и карточки '
    'с прямыми ссылками. delivery — населённые пункты доставки бетона. '
    'documents — опубликованные документы и ссылки на файлы. vacancies — открытые вакансии.',
    {'dataset': {'type': 'string', 'enum': list(DATASETS)}},
    ['dataset'],
)
def _product_categories(site):
    return ['overview', *PRODUCT_SECTIONS, *(GANIN_PRODUCT_ROUTES if site == 'ganin' else ())]


def available_tools(site):
    description = (
        'Каталог продукции. overview — направления, concrete — бетон и растворы, precast — ЖБИ, '
        'asphalt — асфальт, aggregates — щебень, песок и другие материалы карьера. '
        'Для конкретного изделия ЖБИ укажи его название или обозначение в query, например ФБС.'
    )
    if site == 'ganin':
        description += ' cement — фасованный цемент, mineral_powder — минеральный порошок, formwork — опалубка UPEX.'
    products = _function(
        'read_product_catalog', description,
        {
            'category': {'type': 'string', 'enum': _product_categories(site)},
            'query': {'type': 'string', 'description': 'Название или марка конкретного изделия ЖБИ.'},
        },
        ['category'],
    )
    return [SEARCH, products, CATALOG] if site == 'ganin' else [SEARCH, products]


def execute_tool(site, function):
    """Validate the requested operation and bound how much public text it returns."""
    try:
        name = function['name']
        arguments = json.loads(function['arguments'])
    except (KeyError, TypeError, ValueError):
        return {'error': 'Некорректные параметры инструмента.'}, []
    if not isinstance(arguments, dict):
        return {'error': 'Некорректные параметры инструмента.'}, []

    query = arguments.get('query')
    if name == 'search_public_pages' and arguments.keys() == {'query'} and isinstance(query, str):
        query = query.strip()
        if not query or len(query) > 240:
            return {'error': 'Для поиска нужны ключевые слова до 240 символов.'}, []
        entries = search_pages(query, site=site, limit=5)
    elif name == 'read_public_catalog' and site == 'ganin' and arguments.keys() == {'dataset'}:
        dataset = arguments['dataset']
        if not isinstance(dataset, str) or dataset not in DATASETS:
            return {'error': 'Такого справочника нет.'}, []
        entries = DATASETS[dataset]()
    elif name == 'read_product_catalog' and 'category' in arguments and arguments.keys() <= {'category', 'query'}:
        category = arguments['category']
        query = arguments.get('query', '')
        if (not isinstance(category, str) or category not in _product_categories(site)
                or not isinstance(query, str) or len(query) > 240):
            return {'error': 'Некорректный раздел или запрос каталога.'}, []
        entries = product_knowledge(site, category, query)
    else:
        return {'error': 'Инструмент недоступен или параметры не подходят.'}, []

    results = []
    remaining = MAX_RESULT_CHARS
    for entry in entries:
        size = len(entry['title']) + len(entry['url']) + len(entry['excerpt'])
        if size > remaining:
            break
        results.append(entry)
        remaining -= size
    return {'entries': results, 'truncated': len(results) < len(entries)}, results
