# -*- coding: utf-8 -*-
"""Уведомления о новых заявках — на почту и в телеграм.

Главное правило: заявка уже сохранена в базе, поэтому сбой отправки НИКОГДА
не должен ломать ответ клиенту. Все ошибки только пишутся в лог.
Адреса и токен задаются в админке («Общие данные сайта»), поэтому их можно
поменять без программиста.
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'
TIMEOUT = 5


def _telegram(text: str, token: str, chat_id: str) -> None:
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': 'true',
    }).encode()
    req = urllib.request.Request(TELEGRAM_API.format(token=token), data=data)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = json.loads(resp.read().decode())
        if not body.get('ok'):
            log.warning('Телеграм не принял сообщение: %s', body)


def notify(subject: str, lines: list[str]) -> None:
    """Отправить уведомление о заявке. Молча переживает любые сбои."""
    from core.models import SiteSettings

    try:
        site = SiteSettings.get()
    except Exception:                                   # noqa: BLE001
        log.exception('Не удалось прочитать настройки сайта для уведомления')
        return

    text = '\n'.join([subject, ''] + lines)

    recipients = site.notify_email_list
    if recipients:
        try:
            send_mail(
                subject=subject,
                message=text,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception:                               # noqa: BLE001
            log.exception('Не удалось отправить письмо о заявке')

    if site.telegram_token and site.telegram_chat_id:
        try:
            _telegram(text, site.telegram_token, site.telegram_chat_id)
        except (urllib.error.URLError, OSError, ValueError):
            log.exception('Не удалось отправить заявку в телеграм')
        except Exception:                               # noqa: BLE001
            log.exception('Неожиданная ошибка при отправке в телеграм')


def notify_lead(lead) -> None:
    notify('Новая заявка ТКП — ГАНИН ГРУПП', [
        f'Имя: {lead.name}',
        f'Телефон: {lead.phone}',
        f'Компания: {lead.company or "—"}',
        f'Объект / объём / сроки: {lead.details or "—"}',
        f'Страница: {lead.page or "—"}',
    ])


def notify_hauler(app) -> None:
    notify('Новая заявка перевозчика — ГАНИН ГРУПП', [
        f'Имя: {app.name}',
        f'Телефон: {app.phone}',
        f'Техника: {app.vehicles or "—"}',
    ])


def notify_application(app) -> None:
    notify('Новый отклик на вакансию — ГАНИН ГРУПП', [
        f'Имя: {app.name}',
        f'Телефон: {app.phone}',
        f'Вакансия: {app.vacancy or app.vacancy_title or "—"}',
        f'Резюме: {"приложено" if app.resume else "нет"}',
    ])
