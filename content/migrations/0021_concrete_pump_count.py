import re

from django.db import migrations


def update_count(apps, schema_editor):
    fields = [
        ('content', 'Stat', 'note'),
        ('content', 'Direction', 'tagline'),
        ('content', 'Direction', 'asset_text'),
        ('core', 'Page', 'seo_description'),
        ('core', 'Card', 'text'),
    ]
    old = re.compile(r'\b8 бетононасосов\b')
    for app, model, field in fields:
        records = apps.get_model(app, model).objects.using(schema_editor.connection.alias)
        for record in records.filter(**{f'{field}__contains': '8 бетононасосов'}):
            value = getattr(record, field)
            updated = old.sub('10 собственных автобетононасосов', value)
            if updated != value:
                records.filter(pk=record.pk, **{field: value}).update(**{field: updated})


class Migration(migrations.Migration):
    dependencies = [('content', '0020_projectsupply'), ('core', '0015_calculator_quote_copy')]
    operations = [migrations.RunPython(update_count)]
