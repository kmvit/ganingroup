from django.db import migrations


def update_developer_solution_cards(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    Card = apps.get_model('core', 'Card')
    page = Page.objects.filter(slug='reshenie_zastroyshchikam').first()
    if page is None:
        return
    changes = (
        ('Объёмы на пике сезона',
         'Поставка с двух смесительных узлов — пиковая подача до 4000 м³ в сутки',
         'Поставка с 4 смесительных узлов — пиковая подача до 4000 м³ в сутки.'),
        ('Насосы на площадке',
         '8 бетононасосов группы — подача на высоту без субподряда',
         '10 бетононасосов группы — подача на высоту без субподряда'),
    )
    for title, old_text, new_text in changes:
        Card.objects.filter(page_id=page.pk, section='grid1', title=title,
                            text=old_text).update(text=new_text)


class Migration(migrations.Migration):
    dependencies = [('core', '0013_shorten_about_heading')]
    operations = [migrations.RunPython(update_developer_solution_cards,
                                       migrations.RunPython.noop)]
