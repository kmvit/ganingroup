import json
from datetime import timedelta
from io import BytesIO, StringIO
from urllib.error import HTTPError
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from content.models import CatalogItem, Department, Document, ProjectObject, TeamMember
from leads.models import Lead

from .knowledge import PageParser, normalized_url, search_pages
from .models import ChatMessage, ChatSession, DailyIPUsage, KnowledgePage
from .site_tools import execute_tool
from .views import _model_reply


class KnowledgeTests(TestCase):
    def test_team_contacts_are_shared_and_only_published(self):
        TeamMember.objects.create(name='Руководитель', position='Директор')
        Department.objects.create(title='Отдел снабжения', person='Сотрудник снабжения',
                                  phone='+7 800 555-01-23', email='supply@example.org')
        Department.objects.create(title='Неопубликованный отдел', phone='скрытый телефон', published=False)
        TeamMember.objects.create(name='Неопубликованный сотрудник', published=False)
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/kontakty',
                                     title='Контакты', content='Общий сотрудник: +7 800 555-00-11')
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/other',
                                     title='Другой раздел', content='Не относится к общей команде')
        results = []
        for site in ('ganin', 'sd2'):
            result, sources = execute_tool(site, {'name': 'read_company_team', 'arguments': '{}'})
            self.assertIn('+7 800 555-01-23', str(result))
            self.assertIn('supply@example.org', str(result))
            self.assertIn('Руководитель', str(result))
            self.assertIn('+7 800 555-00-11', str(result))
            self.assertNotIn('Не относится к общей команде', str(result))
            self.assertNotIn('Неопубликованный', str(result))
            self.assertNotIn('скрытый телефон', str(result))
            self.assertIn('https://ganin-group.ru/kontakty/', [source['url'] for source in sources])
            results.append(result)
        self.assertEqual(*results)

    def test_daily_cleanup_keeps_dialogues(self):
        session = ChatSession.objects.create(site='sd2', ip_digest='a' * 64,
                                             consent_version='2026-11-05')
        ChatSession.objects.filter(pk=session.pk).update(created_at=timezone.now() - timedelta(days=31))
        ChatMessage.objects.create(session=session, role='user', text='Вопрос о бетоне')
        DailyIPUsage.objects.create(day=timezone.localdate() - timedelta(days=1),
                                    ip_digest='a' * 64, count=2)
        call_command('purge_assistant_data', stdout=StringIO())
        self.assertTrue(ChatSession.objects.filter(pk=session.pk).exists())
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 1)
        self.assertEqual(DailyIPUsage.objects.count(), 0)

    def test_parser_and_search(self):
        parser = PageParser()
        parser.feed('<title>Доставка бетона</title><header>Меню</header><main><h1>Доставка бетона</h1><p>Возим бетон в пункты более 200 км от завода по согласованию с диспетчерской.</p></main>')
        self.assertNotIn('Меню', ''.join(parser.text))
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/dostavka/',
                                     title='Доставка бетона', content=''.join(parser.text))
        result = search_pages('Доставка бетона 200 км')
        self.assertEqual(result[0]['url'], 'https://sd2-kmv.ru/dostavka/')
        self.assertIsNone(normalized_url('https://sd2-kmv.ru/', 'https://evil.example/', 'sd2-kmv.ru'))

    def test_model_cannot_choose_another_site_or_read_unlisted_data(self):
        for site, function in (
            ('sd2', {'name': 'search_public_pages', 'arguments': '{"query":"бетон","site":"ganin"}'}),
            ('sd2', {'name': 'read_public_catalog', 'arguments': '{"dataset":"projects"}'}),
            ('ganin', {'name': 'read_public_catalog', 'arguments': '{"dataset":"leads"}'}),
        ):
            with self.subTest(site=site, function=function):
                result, sources = execute_tool(site, function)
                self.assertIn('error', result)
                self.assertEqual(sources, [])

    def test_product_lookup_prefers_sd2_and_uses_local_reference_as_fallback(self):
        CatalogItem.objects.create(section='produkciya_zhbi', title='Локальные кольца КС', chips='КС15')
        CatalogItem.objects.create(section='produkciya_zhbi', title='Скрытое изделие', published=False)
        product_url = 'https://sd2-kmv.ru/zhelezobeton/cena-na-FBS-bloki-fundamentnye'
        KnowledgePage.objects.create(site='sd2', url=product_url, title='Блоки ФБС',
                                     content='ФБС 24-5-6: длина 2380 мм.')
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/kontakty', title='Контакты ФБС',
                                     content='Страница вне каталога.')
        function = {
            'name': 'read_product_catalog', 'arguments': '{"category":"precast","query":"ФБС"}',
        }
        result, sources = execute_tool('ganin', function)
        self.assertFalse(result['truncated'])
        self.assertEqual(sources[0]['url'], product_url)
        self.assertIn('2380 мм', sources[0]['excerpt'])
        self.assertNotIn('Локальные кольца КС', str(result))
        self.assertNotIn('Страница вне каталога', str(result))
        KnowledgePage.objects.filter(url=product_url).delete()
        result, sources = execute_tool('ganin', function)
        self.assertIn('Локальные кольца КС', sources[0]['excerpt'])
        self.assertNotIn('Скрытое изделие', str(result))

    def test_document_lookup_returns_public_download_links(self):
        Document.objects.create(title='Реквизиты', file='docs/details.pdf')
        Document.objects.create(title='Черновик', published=False, file='docs/draft.pdf')
        _, sources = execute_tool('ganin', {
            'name': 'read_public_catalog', 'arguments': '{"dataset":"documents"}',
        })
        self.assertIn('https://ganin-group.ru/media/docs/details.pdf', [entry['url'] for entry in sources])
        self.assertNotIn('Черновик', [entry['title'] for entry in sources])

    def test_html_index_keeps_table_columns_separate(self):
        parser = PageParser()
        parser.feed('<table><tr><th>Марка</th>\n  <th>Класс</th></tr>'
                    '<tr><td>М300<br>П3</td>\n  <td>В22,5</td></tr></table>')
        self.assertIn('М300 / П3 | В22,5', ''.join(parser.text))

    def test_public_page_lookup_reads_exact_link_without_external_fetches(self):
        url = 'https://sd2-kmv.ru/kontakty'
        KnowledgePage.objects.create(site='sd2', url=url, title='Контакты',
                                     content='Отдел снабжения и рабочие телефоны.')
        _, sources = execute_tool('ganin', {
            'name': 'read_public_page', 'arguments': json.dumps({'url': url}),
        })
        self.assertEqual([source['url'] for source in sources], [url])
        for unsafe in ('https://example.org/kontakty', 'https://sd2-kmv.ru@evil.example/kontakty'):
            result, sources = execute_tool('ganin', {
                'name': 'read_public_page', 'arguments': json.dumps({'url': unsafe}),
            })
            self.assertIn('error', result)
            self.assertEqual(sources, [])

    def test_general_directions_do_not_return_careers(self):
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/kariera/',
                                     title='Работа в ГАНИН ГРУПП',
                                     content='Направления работы компании и открытые вакансии.')
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/consent/',
                                     title='Согласие на обработку данных',
                                     content='Работа компании с обращениями и направления обработки.')
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/',
                                     title='ГАНИН ГРУПП — производство',
                                     content='Направления: бетон, ЖБИ, асфальт и карьер.')
        sources = search_pages('Какие направления работы у ГАНИН ГРУПП?', site='ganin')
        self.assertEqual([source['url'] for source in sources], ['https://ganin-group.ru/'])

    def test_search_prefers_relevant_page_on_requested_site(self):
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/kariera/',
                                     title='Работа в ГАНИН ГРУПП',
                                     content='Открытые позиции — по телефону отдела персонала.')
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/policy/',
                                     title='Политика обработки данных',
                                     content='Приём откликов на вакансии и обработка обращений.')
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/dostavka/',
                                     title='Доставка бетона миксером и аренда бетононасоса',
                                     content='Миксеры на 3, 5, 7, 9, 10, 12 и 14 м³. 10 собственных автобетононасосов.\nСтоимость рейса зависит от объёма.')
        self.assertEqual(search_pages('Есть ли вакансии?', site='ganin')[0]['url'],
                         'https://ganin-group.ru/kariera/')
        sources = search_pages('Какие объёмы миксеров и есть ли бетононасос?', site='sd2')
        self.assertEqual([item['url'] for item in sources], ['https://sd2-kmv.ru/dostavka/'])
        self.assertIn('3, 5, 7', sources[0]['excerpt'])

    def test_contact_question_finds_address_and_phone(self):
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/kontakty/',
                                     title='Контакты ГАНИН ГРУПП — телефоны',
                                     content='Контакты ГАНИН ГРУПП — телефоны\nОтдел продаж: +7 928 821-72-11.\nАдрес: Пятигорск, Черкесское шоссе, 2.\nМенеджер перезвонит.')
        sources = search_pages('Где находится завод и как позвонить менеджеру?', site='ganin')
        self.assertEqual(sources[0]['url'], 'https://ganin-group.ru/kontakty/')
        self.assertIn('Черкесское', sources[0]['excerpt'])
        self.assertIn('+7 928 821-72-11', sources[0]['excerpt'])

    @override_settings(ASSISTANT_ENABLED=False)
    def test_disabled_when_flag_is_off(self):
        response = self.client.post('/assistant/chat/', data='{}', content_type='application/json',
                                    HTTP_ORIGIN='https://ganin-group.ru')
        self.assertEqual(response.status_code, 404)


@override_settings(ASSISTANT_ENABLED=True, ASSISTANT_DAILY_LIMIT_ENABLED=False)
class AssistantApiTests(TestCase):
    def setUp(self):
        KnowledgePage.objects.create(site='sd2', url='https://sd2-kmv.ru/dostavka/',
                                     title='Доставка бетона',
                                     content='Возим бетон в пункты более 200 км от завода по согласованию с диспетчерской.')

    def test_chat_uses_sources_and_cors(self):
        with patch('assistant.views._model_reply', return_value=(
            'Доставляем по согласованию.',
            [{'title': 'Доставка бетона', 'url': 'https://sd2-kmv.ru/dostavka/'}],
        )):
            response = self.client.post('/assistant/chat/',
                                        data=json.dumps({'message': 'Доставка бетона 200 км?'}),
                                        content_type='application/json',
                                        HTTP_ORIGIN='https://sd2-kmv.ru')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'https://sd2-kmv.ru')
        self.assertEqual(response.json()['sources'][0]['url'], 'https://sd2-kmv.ru/dostavka/')
        session = ChatSession.objects.get(pk=response.json()['session_id'])
        self.assertIsNone(session.consent_at)
        self.assertEqual(list(session.messages.values_list('role', 'text')), [
            ('user', 'Доставка бетона 200 км?'), ('assistant', 'Доставляем по согласованию.'),
        ])
        self.assertFalse(DailyIPUsage.objects.exists())

    @override_settings(ASSISTANT_API_URL='https://gateway.example', ASSISTANT_API_KEY='test-key')
    def test_model_requests_only_needed_catalog_data(self):
        ProjectObject.objects.update(published=False)
        obj = ProjectObject.objects.create(title='ЖК «Замковая»', city='Кисловодск')
        ProjectObject.objects.create(title='Черновик проекта', published=False)
        KnowledgePage.objects.create(site='ganin', url='https://ganin-group.ru/uslugi/laboratoriya/',
                                     title='Лаборатория', content='Испытание прочности бетона.')
        tool_call = {
            'id': 'catalog-1', 'type': 'function',
            'function': {'name': 'read_public_catalog', 'arguments': '{"dataset":"projects"}'},
        }
        responses = [
            {'role': 'assistant', 'content': None, 'tool_calls': [tool_call]},
            {'role': 'assistant', 'content': 'Кисловодск — 1 объект.'},
        ]

        def gateway_response(request, timeout):
            requests.append(json.loads(request.data))
            return BytesIO(json.dumps({'choices': [{'message': responses.pop(0)}]}).encode())

        requests = []
        with patch('assistant.views.urlopen', side_effect=gateway_response):
            response = self.client.post('/assistant/chat/',
                                        data=json.dumps({'message': 'В каком городе больше всего ваших объектов?'}),
                                        content_type='application/json',
                                        HTTP_ORIGIN='https://ganin-group.ru')
        self.assertEqual(response.status_code, 200)
        first = requests[0]['messages']
        self.assertEqual('В каком городе больше всего ваших объектов?', first[1]['content'])
        self.assertNotIn('ЖК «Замковая»', first[0]['content'])
        result = next(message for message in requests[1]['messages'] if message['role'] == 'tool')
        self.assertEqual(result['tool_call_id'], 'catalog-1')
        self.assertIn('Кисловодск — 1', result['content'])
        self.assertNotIn('Испытание прочности бетона.', result['content'])
        self.assertNotIn('Черновик проекта', result['content'])
        self.assertEqual(response.json()['sources'], [{
            'title': obj.title, 'url': 'https://ganin-group.ru' + reverse('obekt', args=[obj.slug]),
        }])

    @override_settings(ASSISTANT_DAILY_LIMIT_ENABLED=True, ASSISTANT_TRUST_X_REAL_IP=False)
    @patch('assistant.views._model_reply', return_value=('Ответ', []))
    def test_chat_without_consent_has_shared_daily_limit(self, model):
        body = json.dumps({'message': 'Напиши стих про бетон'})
        origins = ('https://ganin-group.ru', 'https://sd2-kmv.ru')
        for i in range(100):
            response = self.client.post('/assistant/chat/', data=body, content_type='application/json',
                                        HTTP_ORIGIN=origins[i % 2], REMOTE_ADDR='192.0.2.1')
            self.assertEqual(response.status_code, 200, i)
        response = self.client.post('/assistant/chat/', data=body, content_type='application/json',
                                    HTTP_ORIGIN=origins[1], REMOTE_ADDR='192.0.2.1')
        self.assertEqual(response.status_code, 429)
        self.assertIn('100 вопросов', response.json()['error'])
        self.assertEqual(DailyIPUsage.objects.get().count, 100)
        response = self.client.post('/assistant/chat/', data=body, content_type='application/json',
                                    HTTP_ORIGIN=origins[1], REMOTE_ADDR='192.0.2.2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatSession.objects.count(), 101)
        self.assertEqual(ChatMessage.objects.count(), 202)

    def test_invalid_session_id_starts_a_new_recorded_dialogue(self):
        with patch('assistant.views._model_reply', return_value=('Ответ', [])):
            response = self.client.post('/assistant/chat/',
                                        data=json.dumps({'message': 'Доставка бетона 200 км?',
                                                         'session_id': '11111111-1111-4111-8111-111111111111'}),
                                        content_type='application/json',
                                        HTTP_ORIGIN='https://sd2-kmv.ru')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['session_id'], '11111111-1111-4111-8111-111111111111')
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 2)

    def test_other_origin_is_rejected(self):
        response = self.client.post('/assistant/chat/', data='{}', content_type='application/json',
                                    HTTP_ORIGIN='https://other.example')
        self.assertEqual(response.status_code, 403)

    def test_history_is_not_taken_from_another_site_or_ip(self):
        session = ChatSession.objects.create(site='sd2', ip_digest='0' * 64,
                                             consent_version='recording-v1', consent_at=None)
        ChatMessage.objects.create(session=session, role='user', text='Чужой диалог')
        for origin in ('https://ganin-group.ru', 'https://sd2-kmv.ru'):
            with self.subTest(origin=origin), patch(
                'assistant.views._model_reply', return_value=('Ответ', []),
            ) as model:
                response = self.client.post('/assistant/chat/', data=json.dumps({
                    'message': 'Что еще производите?', 'session_id': str(session.pk),
                }), content_type='application/json', HTTP_ORIGIN=origin)
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response.json()['session_id'], str(session.pk))
            self.assertEqual(model.call_args.kwargs['history'], [])

    def test_short_follow_up_uses_previous_topic_locally(self):
        KnowledgePage.objects.create(site='sd2',
                                     url='https://sd2-kmv.ru/zhelezobeton/cena-na-FBS-bloki-fundamentnye',
                                     title='Блоки ФБС',
                                     content='Фундаментные блоки ФБС доступны в девяти типоразмерах.\nТипоразмеры: ФБС 24-5-6 т и ФБС 12-4-6 т.')
        with patch('assistant.views._model_reply', return_value=('Есть девять типоразмеров.', [])) as model:
            response = self.client.post('/assistant/chat/',
                                        data=json.dumps({'message': 'Есть ли блоки ФБС?'}),
                                        content_type='application/json', HTTP_ORIGIN='https://sd2-kmv.ru')
            response = self.client.post('/assistant/chat/',
                                        data=json.dumps({'message': 'А какие размеры?',
                                                         'session_id': response.json()['session_id']}),
                                        content_type='application/json', HTTP_ORIGIN='https://sd2-kmv.ru')
        self.assertEqual(response.status_code, 200)
        args, kwargs = model.call_args
        self.assertEqual(kwargs['history'], [
            {'role': 'user', 'content': 'Есть ли блоки ФБС?'},
            {'role': 'assistant', 'content': 'Есть девять типоразмеров.'},
        ])
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 4)

    def test_contacts_and_address_are_preserved_and_passed_to_model(self):
        question = 'Я Иван, мой телефон +7 928 123-45-67. Бетон на улицу Ленина 10.'
        with patch('assistant.views._model_reply', return_value=('Уточните объём.', [])) as model:
            response = self.client.post('/assistant/chat/', data=json.dumps({'message': question}),
                                        content_type='application/json', HTTP_ORIGIN='https://ganin-group.ru')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(model.call_args.args[0], question)
        self.assertEqual(ChatMessage.objects.get(role='user').text, question)

    @override_settings(ASSISTANT_API_URL='https://gateway.example', ASSISTANT_API_KEY='test-key')
    def test_last_ten_messages_include_answers_and_preserve_current_question(self):
        session = ChatSession.objects.create(site='ganin', ip_digest='a'*64, consent_version='recording-v1')
        for i in range(6):
            ChatMessage.objects.create(session=session, role='user', text=f'Вопрос {i}')
            ChatMessage.objects.create(session=session, role='assistant', text=f'Ответ {i}')
        current = 'Возможно ли поставка на объект 1000м3 за один день?'
        gateway_answer = {'choices': [{'message': {'role': 'assistant', 'content': 'Ответ'}}]}
        with patch('assistant.views._get_session', return_value=session), patch(
            'assistant.views.urlopen', return_value=BytesIO(json.dumps(gateway_answer).encode()),
        ) as gateway:
            response = self.client.post('/assistant/chat/', data=json.dumps({'message': current}),
                                        content_type='application/json', HTTP_ORIGIN='https://ganin-group.ru')
        self.assertEqual(response.status_code, 200)
        messages = json.loads(gateway.call_args.args[0].data)['messages']
        self.assertEqual(len(messages), 12)
        self.assertEqual(messages[1], {'role': 'user', 'content': 'Вопрос 1'})
        self.assertEqual(messages[-2], {'role': 'assistant', 'content': 'Ответ 5'})
        self.assertEqual(messages[-1], {'role': 'user', 'content': current})

    @override_settings(ASSISTANT_API_URL='https://gateway.example', ASSISTANT_API_KEY='test-key')
    def test_new_topic_reaches_model_in_original_form(self):
        current = 'кто президент америки'
        history = [
            {'role': 'user', 'content': 'А опалубку делаете?'},
            {'role': 'assistant', 'content': 'Предлагаем опалубку.'},
        ]
        message = {'choices': [{'message': {'role': 'assistant', 'content': None, 'tool_calls': [{
            'id': 'direct-1', 'type': 'function', 'function': {
                'name': 'reply_without_lookup',
                'arguments': json.dumps({'kind': 'off_topic', 'text': 'Я отвечаю только о сайте.'}),
            },
        }]}}]}
        with patch('assistant.views.urlopen', return_value=BytesIO(json.dumps(message).encode())) as gateway:
            _model_reply(current, site='ganin', history=history)
        messages = json.loads(gateway.call_args.args[0].data)['messages']
        self.assertEqual(messages[1:3], history)
        self.assertEqual(messages[-1], {'role': 'user', 'content': current})

    @override_settings(ASSISTANT_API_URL='https://gateway.example', ASSISTANT_API_KEY='test-key')
    def test_site_identity_and_full_assortment_follow_up_are_preserved(self):
        history = [
            {'role': 'user', 'content': 'Что еще производите'},
            {'role': 'assistant', 'content': 'Производство какого материала вас интересует?'},
        ]
        answer = {'choices': [{'message': {'role': 'assistant', 'content': None, 'tool_calls': [{
            'id': 'direct-1', 'type': 'function', 'function': {
                'name': 'reply_without_lookup',
                'arguments': json.dumps({'kind': 'clarification', 'text': 'Уточните запрос.'}),
            },
        }]}}]}
        for site, name, other in (('ganin', 'ГАНИН ГРУПП', 'Стройдеталь-2'),
                                  ('sd2', 'Стройдеталь-2', 'ГАНИН ГРУПП')):
            with self.subTest(site=site), patch(
                'assistant.views.urlopen', return_value=BytesIO(json.dumps(answer).encode()),
            ) as gateway:
                _model_reply('Весь спектр', site=site, history=history)
            messages = json.loads(gateway.call_args.args[0].data)['messages']
            self.assertTrue(messages[0]['content'].startswith(f'Ты ассистент сайта «{name}»'))
            self.assertIn(f'работе сайта «{name}»', messages[0]['content'])
            self.assertNotIn(f'работе сайта «{other}»', messages[0]['content'])
            self.assertEqual(messages[1:-1], history)
            self.assertEqual(messages[-1]['content'], 'Весь спектр')

    def test_gateway_rate_limit_is_explained(self):
        with patch('assistant.views._model_reply', side_effect=HTTPError('https://gateway.example', 429, 'limit', {}, None)):
            response = self.client.post('/assistant/chat/', data=json.dumps({'message': 'Доставка бетона?'}),
                                        content_type='application/json', HTTP_ORIGIN='https://sd2-kmv.ru')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(ChatMessage.objects.count(), 2)

    @override_settings(ASSISTANT_API_URL='https://gateway.example', ASSISTANT_API_KEY='test-key')
    def test_model_cannot_publish_an_invented_link(self):
        content = 'Подробнее [бетон](https://sd2.ru/concrete).'
        search = {'role': 'assistant', 'content': None, 'tool_calls': [{
            'id': 'search-1', 'type': 'function',
            'function': {'name': 'search_public_pages', 'arguments': '{"query":"бетон"}'},
        }]}
        source = {'title': 'Бетон', 'url': 'https://sd2-kmv.ru/cena-betona-s-dostavkoj',
                  'excerpt': 'Бетон М200.'}
        with patch('assistant.views._model_message', side_effect=[search, {'role': 'assistant', 'content': content}]), patch(
            'assistant.views.execute_tool', return_value=({'entries': [source]}, [source]),
        ):
            text, _ = _model_reply('Как получить прайс?', site='ganin')
        self.assertNotIn('https://sd2.ru', text)
        self.assertIn('бетон', text)

    def test_model_cannot_answer_facts_without_lookup(self):
        with patch('assistant.views._model_message', return_value={
            'role': 'assistant', 'content': 'Наша мощность 200 м³/час.',
        }):
            with self.assertRaisesMessage(ValueError, 'no supporting tool results'):
                _model_reply('Поставите 1000 м³ за день?', site='ganin')

    @patch('assistant.views.notify_lead')
    def test_lead_requires_consent_and_saves_source(self, notify):
        data = {'name': 'Иван', 'phone': '+7 928 123-45-67', 'details': 'Бетон М300, 20 м³',
                'page': 'https://sd2-kmv.ru/dostavka/', 'agree': False}
        headers = {'HTTP_ORIGIN': 'https://sd2-kmv.ru'}
        response = self.client.post('/assistant/lead/', data=json.dumps(data),
                                    content_type='application/json', **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)
        data['agree'] = True
        response = self.client.post('/assistant/lead/', data=json.dumps(data),
                                    content_type='application/json', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('sd2:', Lead.objects.get().page)
        notify.assert_called_once()
