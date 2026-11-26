from django.db import migrations


def update_road_solution_standard(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    Card = apps.get_model('core', 'Card')
    page = Page.objects.filter(slug='reshenie_dorozhnikam').first()
    if page is None:
        return
    Card.objects.filter(
        page_id=page.pk,
        section='grid1',
        title='Асфальтобетон по ГОСТ',
        text='Смеси по ГОСТ 9128-2009 — песчаные и мелкозернистые',
    ).update(text='Смеси по ГОСТ Р 58406.2-2020 — песчаные и мелкозернистые')


class Migration(migrations.Migration):
    dependencies = [('core', '0015_calculator_quote_copy')]
    operations = [migrations.RunPython(update_road_solution_standard,
                                       migrations.RunPython.noop)]
