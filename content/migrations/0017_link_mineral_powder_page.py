from django.db import migrations


def link_page(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    MenuItem = apps.get_model('core', 'MenuItem')
    Direction = apps.get_model('content', 'Direction')

    page = Page.objects.filter(slug='produkciya_mineralnyy_poroshok').first()
    if not page:
        return
    Direction.objects.filter(url_name='produkciya_mineralnyy_poroshok').update(page=page)
    menu = MenuItem.objects.filter(parent__title='Продукция',
                                   url_name='produkciya_mineralnyy_poroshok').first()
    if menu:
        menu.page = page
        menu.url_name = ''
        menu.save(update_fields=['page', 'url_name'])


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0016_direction_page'),
        ('core', '0010_menuitem_page_page_product_slug_page_video_file_and_more'),
    ]

    operations = [migrations.RunPython(link_page, migrations.RunPython.noop)]
