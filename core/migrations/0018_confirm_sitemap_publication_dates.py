from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import migrations
from django.utils import timezone


def set_publication_dates(apps, schema_editor):
    alias = schema_editor.connection.alias
    pages = apps.get_model('core', 'Page').objects.using(alias)
    projects = apps.get_model('content', 'ProjectObject').objects.using(alias)
    # e7db665 changed the catalogue and 016b656 published the supply table on 26 November.
    published = datetime(2026, 11, 26, tzinfo=ZoneInfo('Europe/Moscow'))
    pages.filter(slug='produkciya', updated_at__lt=published).update(updated_at=published)
    projects.filter(slug='kislovodsk-zhk-zamkovaya', supply__confirmed=True,
                    updated_at__lt=published).update(updated_at=published)
    # The calculator changes again in this release.
    now = timezone.now()
    pages.filter(slug__in=('kalkulyator', 'laboratoriya'), updated_at__lt=now).update(updated_at=now)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_update_laboratory_photo'),
        ('content', '0023_asphalt_direction_standard'),
    ]
    operations = [migrations.RunPython(set_publication_dates, migrations.RunPython.noop)]
