# -*- coding: utf-8 -*-
"""Завести документы (сертификаты и декларации) в блок «Документы».

Файлы должны уже лежать в media/docs/. Команда только создаёт записи в БД
и привязывает их к файлам — идемпотентно (get_or_create по названию), поэтому
её безопасно запускать и локально, и на сервере.

Запуск:  python manage.py seed_documents
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from content.docs_seed import DOCS, OBSOLETE_TITLES
from content.models import Document


class Command(BaseCommand):
    help = 'Создаёт записи документов из файлов в media/docs/'

    def handle(self, *args, **opts):
        docs_dir = Path(settings.MEDIA_ROOT) / 'docs'
        created = linked = missing = 0
        for i, (fname, title, kind, summary) in enumerate(DOCS, 1):
            if not (docs_dir / fname).exists():
                self.stdout.write(self.style.WARNING(f'  нет файла: {fname}'))
                missing += 1
                continue
            doc, was_created = Document.objects.get_or_create(
                title=title, defaults=dict(kind=kind, summary=summary, order=i * 10))
            created += was_created
            if not doc.file:
                doc.file.name = f'docs/{fname}'          # файл уже в media/docs/
                doc.save(update_fields=['file'])
                linked += 1
        # убрать старые записи-заглушки без файлов (из первичного seed)
        removed, _ = Document.objects.filter(
            title__in=OBSOLETE_TITLES, file='').delete()
        self.stdout.write(self.style.SUCCESS(
            f'Готово. Новых: {created}, привязано файлов: {linked}, '
            f'нет файла: {missing}, удалено заглушек: {removed}'))
