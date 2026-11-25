from django.db import migrations


def update_subtitle(apps, schema_editor):
    pages = apps.get_model('core', 'Page').objects.using(schema_editor.connection.alias)
    old = 'Результат переносится в заявку на ТКП.'
    for page in pages.filter(slug='kalkulyator', subtitle__contains=old):
        page.subtitle = page.subtitle.replace(old, 'Марка и объём переносятся в запрос цены с доставкой.')
        page.save(update_fields=['subtitle'])


class Migration(migrations.Migration):
    dependencies = [('core', '0014_update_developer_solution_cards')]
    operations = [migrations.RunPython(update_subtitle)]
