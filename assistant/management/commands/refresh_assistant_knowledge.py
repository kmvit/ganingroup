from django.core.management.base import BaseCommand, CommandError

from assistant.knowledge import ROOTS, refresh_site


class Command(BaseCommand):
    help = 'Обновить базу знаний ассистента по публичным страницам обоих сайтов'

    def add_arguments(self, parser):
        parser.add_argument('--site', choices=ROOTS, help='Обновить только один сайт')

    def handle(self, *args, **options):
        failed = []
        for site in ([options['site']] if options['site'] else ROOTS):
            count = refresh_site(site)
            self.stdout.write(f'{site}: обновлено {count} страниц')
            if not count:
                failed.append(site)
        if failed:
            raise CommandError('Не удалось обновить базу знаний: ' + ', '.join(failed))
