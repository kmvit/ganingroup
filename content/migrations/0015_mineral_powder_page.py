from django.db import migrations


VIDEO_URL = 'https://drive.google.com/file/d/1NqBBJxi7_O0FZd4zRY6EZpqJ3pO7DVMO/view?usp=sharing'


def create_page(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    MenuItem = apps.get_model('core', 'MenuItem')
    Direction = apps.get_model('content', 'Direction')

    Page.objects.get_or_create(
        slug='produkciya_mineralnyy_poroshok',
        defaults={
            'admin_title': 'Минеральный порошок',
            'h1': 'Минеральный порошок',
            'subtitle': 'Минеральный порошок МП-1 и МП-2 собственного производства.',
            'body': 'Минеральный порошок МП-1 и МП-2 — ГОСТ 32761-2014. Оба вида в наличии, цена договорная. Условия отгрузки — самовывоз.',
            'video_url': VIDEO_URL,
            'seo_title': 'Минеральный порошок МП-1 и МП-2 | ГАНИН ГРУПП',
            'seo_description': 'Минеральный порошок МП-1 и МП-2 по ГОСТ 32761-2014. Производство на КМВ.',
        },
    )
    Direction.objects.get_or_create(
        url_name='produkciya_mineralnyy_poroshok',
        defaults={'title': 'Минеральный порошок',
                  'tagline': 'МП-1 и МП-2 по ГОСТ 32761-2014',
                  'order': 55, 'published': True},
    )
    product_menu = MenuItem.objects.filter(parent__isnull=True, title='Продукция').first()
    if product_menu:
        item = MenuItem.objects.filter(parent=product_menu, title__icontains='Минеральн').first()
        if item:
            item.url_name = 'produkciya_mineralnyy_poroshok'
            item.external_url = ''
            item.save(update_fields=['url_name', 'external_url'])
        else:
            MenuItem.objects.create(parent=product_menu, title='Минеральный порошок',
                                    url_name='produkciya_mineralnyy_poroshok',
                                    order=55, published=True)


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0014_directions_to_sd2'),
        ('core', '0009_page_video_url'),
    ]

    operations = [migrations.RunPython(create_page, migrations.RunPython.noop)]
