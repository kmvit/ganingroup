# Бетон, ЖБИ, асфальт и карьер уходят на sd2-kmv.ru, как опалубка на upex.pro:
# своих страниц у направлений больше нет, плитки и пункты меню — внешние ссылки.

from django.db import migrations, models

from content.utils import SD2_URLS


def to_sd2(apps, schema_editor):
    Direction = apps.get_model('content', 'Direction')
    MenuItem = apps.get_model('core', 'MenuItem')
    for url_name, default in SD2_URLS.items():
        url = default
        for d in Direction.objects.filter(url_name=url_name):
            url = d.shop_url or d.external_url or default
            d.external_url = url
            d.save(update_fields=['external_url'])
        for m in MenuItem.objects.filter(url_name=url_name):
            m.url_name = ''
            m.external_url = url
            if not m.title.endswith('↗'):
                m.title = f'{m.title} ↗'
            m.save(update_fields=['url_name', 'external_url', 'title'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0013_direction_shop_url'),
        ('core', '0008_page_updated_at'),
    ]

    operations = [
        migrations.RunPython(to_sd2, migrations.RunPython.noop),
        migrations.RemoveField(model_name='direction', name='shop_url'),
        migrations.AlterField(
            model_name='direction',
            name='external_url',
            field=models.URLField(blank=True, help_text='Если задана — плитка ведёт на другой сайт: UPEX → upex.pro, бетон/ЖБИ/асфальт/карьер → sd2-kmv.ru', verbose_name='Внешняя ссылка'),
        ),
        migrations.AlterField(
            model_name='direction',
            name='url_name',
            field=models.CharField(blank=True, help_text='Имя URL внутренней страницы, например produkciya_cement. Служит и ключом направления — не менять', max_length=60, verbose_name='Маршрут страницы'),
        ),
    ]
