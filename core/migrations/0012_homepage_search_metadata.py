from django.db import migrations
from django.utils import timezone


OLD = {
    'home': (
        'ГАНИН ГРУПП — бетон, ЖБИ и опалубка | завод на КМВ',
        'Производственная группа на КМВ: свой карьер, завод, лаборатория и автопарк. Бетон и ЖБИ по СКФО, опалубка UPEX по России. Запросите ТКП.',
    ),
    'o_gruppe': (
        'О группе ГАНИН ГРУПП — ЗАО «Стройдеталь-2», Пятигорск',
        'ГАНИН ГРУПП — бренд ЗАО «Стройдеталь-2»: 60+ лет производства на КМВ. Свой карьер, заводы бетона и ЖБИ, лаборатория, автопарк, опалубка UPEX.',
    ),
}

NEW = {
    'home': (
        'ГАНИН ГРУПП — официальный сайт производственной группы на КМВ',
        'ГАНИН ГРУПП — производственная группа на КМВ. Свой карьер, завод, лаборатория и автопарк. Бетон и ЖБИ по СКФО, опалубка UPEX по России.',
    ),
    'o_gruppe': (
        'О группе: история, производство и команда | ГАНИН ГРУПП',
        'История ГАНИН ГРУПП и ЗАО «Стройдеталь-2»: производство на КМВ с 1962 года, карьер, заводы бетона и ЖБИ, лаборатория, автопарк и команда.',
    ),
}


def update_search_metadata(apps, schema_editor):
    Page = apps.get_model('core', 'Page')
    for slug, old_values in OLD.items():
        page = Page.objects.filter(slug=slug).first()
        if page is None:
            continue
        changes = {}
        for field, old, new in zip(('seo_title', 'seo_description'), old_values, NEW[slug]):
            if getattr(page, field) == old:
                changes[field] = new
        if changes:
            changes['updated_at'] = timezone.now()
            Page.objects.filter(pk=page.pk).update(**changes)


class Migration(migrations.Migration):
    dependencies = [('core', '0011_alter_page_video_file_alter_page_video_url')]
    operations = [migrations.RunPython(update_search_metadata, migrations.RunPython.noop)]
