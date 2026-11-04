from django.db import migrations
from django.utils import timezone


OLD_HEADING = 'О группе <em style="font-style:normal;color:var(--accent)">ГАНИН ГРУПП</em>'


def shorten_about_heading(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    Page.objects.filter(slug='o_gruppe', h1=OLD_HEADING).update(
        h1='О группе', updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('core', '0012_homepage_search_metadata')]
    operations = [migrations.RunPython(shorten_about_heading, migrations.RunPython.noop)]
