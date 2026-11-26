from datetime import date
from decimal import Decimal

from django.db import migrations


def publish_supply(apps, schema_editor):
    objects = apps.get_model('content', 'ProjectObject').objects.using(schema_editor.connection.alias)
    supplies = apps.get_model('content', 'ProjectSupply').objects.using(schema_editor.connection.alias)
    project = objects.filter(slug='kislovodsk-zhk-zamkovaya').first()
    if project:
        supplies.get_or_create(project=project, defaults={
            'period': '18.06.2024 — 24.11.2026',
            'grades': 'В12,5 (М150), В20 (М250), В25 (М350), В30 (М400). Также поставлялся цементный раствор М150.',
            'total': Decimal('58183.20'),
            'pour_date': date(2025, 6, 30),
            'pour_volume': Decimal('1374.00'),
            'minutes': 1075,
            'confirmed': True,
        })


class Migration(migrations.Migration):
    dependencies = [('content', '0021_concrete_pump_count')]
    operations = [migrations.RunPython(publish_supply, migrations.RunPython.noop)]
