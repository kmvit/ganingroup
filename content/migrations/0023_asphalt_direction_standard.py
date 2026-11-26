from django.db import migrations


def update_direction(apps, schema_editor):
    directions = apps.get_model('content', 'Direction').objects.using(schema_editor.connection.alias)
    directions.filter(url_name='produkciya_asfalt', tagline__contains='9128-2009').update(
        tagline='Асфальтобетонные смеси по ГОСТ Р 58406.2-2020',
    )


class Migration(migrations.Migration):
    dependencies = [('content', '0022_zamkovaya_supply')]
    operations = [migrations.RunPython(update_direction, migrations.RunPython.noop)]
