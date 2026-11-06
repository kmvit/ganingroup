from django.core.management.base import BaseCommand
from django.utils import timezone

from assistant.models import DailyIPUsage


class Command(BaseCommand):
    help = 'Удалить завершённые суточные счётчики ассистента; диалоги не затрагивать'

    def handle(self, *args, **options):
        usage, _ = DailyIPUsage.objects.filter(day__lt=timezone.localdate()).delete()
        self.stdout.write(f'Удалено суточных счётчиков: {usage}')
