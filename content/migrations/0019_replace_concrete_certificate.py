from pathlib import Path

from django.core.files import File
from django.core.files.storage import default_storage
from django.db import migrations


def replace_certificate(apps, schema_editor):
    documents = apps.get_model('content', 'Document').objects.using(schema_editor.connection.alias)
    source = Path(__file__).resolve().parents[1] / 'assets' / 'sertifikat-beton-2029.pdf'
    target = f'docs/{source.name}'
    if not default_storage.exists(target):
        with source.open('rb') as pdf:
            target = default_storage.save(target, File(pdf))
    documents.filter(file__in=['docs/sertifikat-beton.pdf', target]).update(
        file=target, summary='Действует до 13.09.2029', order=30)
    documents.filter(file='docs/deklaraciya-bst.pdf').update(order=10)
    documents.filter(file='docs/deklaraciya-bsm.pdf').update(order=20)


class Migration(migrations.Migration):
    dependencies = [('content', '0018_correct_object_cards')]
    operations = [migrations.RunPython(replace_certificate)]
