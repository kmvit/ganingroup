from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations


def update_photo(apps, schema_editor):
    pages = apps.get_model('core', 'Page').objects.using(schema_editor.connection.alias)
    page = pages.filter(slug='laboratoriya').first()
    if page is None:
        return

    path = Path(settings.BASE_DIR) / 'static/assets/img/laboratory-testing-equipment.jpg'
    with path.open('rb') as source:
        page.photo.save(path.name, File(source), save=False)
    page.save(update_fields=['photo'])


class Migration(migrations.Migration):
    dependencies = [('core', '0016_update_road_solution_standard')]
    operations = [migrations.RunPython(update_photo, migrations.RunPython.noop)]
