from django.db import migrations


def correct_cards(apps, schema_editor):
    ProjectObject = apps.get_model('content', 'ProjectObject')
    ObjectStat = apps.get_model('content', 'ObjectStat')

    corrections = [
        (
            'rekonstrukciya-aeroporta-mineralnye-vody',
            'Кисловодск ЖК Замковая',
            dict(
                slug='kislovodsk-zhk-zamkovaya',
                city='Кисловодск',
                summary='Поставка бетона для строительства ЖК «Замковая» в Кисловодске.',
                headline='ЖК «Замковая» в Кисловодске',
                context='Строительство жилого комплекса «Замковая» в Кисловодске.',
            ),
        ),
        (
            'mkc-rossiya',
            'Кисловодск Стройжилсервис',
            dict(
                slug='kislovodsk-stroyzhilservis',
                summary='Поставка бетона для объекта «Стройжилсервис» в Кисловодске.',
                headline='Объект «Стройжилсервис» в Кисловодске',
                context='Объект компании «Стройжилсервис» в Кисловодске.',
            ),
        ),
        (
            'masloceh-ao-azovskiy-hleb',
            'Санаторий Русель',
            dict(
                slug='sanatoriy-rusel',
                title='Санаторий Русел',
                summary='Опалубка UPEX для санатория «Русел» в Кисловодске.',
                headline='Опалубка для санатория «Русел»',
                context='Объект санатория «Русел» в Кисловодске.',
            ),
        ),
    ]
    for old_slug, old_title, values in corrections:
        obj = ProjectObject.objects.filter(slug=old_slug, title=old_title).first()
        if not obj:
            continue
        for field, value in values.items():
            setattr(obj, field, value)
        for field in ('challenge', 'solution', 'result', 'quote_text',
                      'quote_author', 'quote_role'):
            setattr(obj, field, '')
        obj.save(update_fields=[*values, 'challenge', 'solution', 'result',
                                'quote_text', 'quote_author', 'quote_role', 'updated_at'])
        # Цифры относились к прежним объектам (аэропорт, МКЦ, маслоцех).
        # Сохраняем записи в админке, но не публикуем как факты о новых объектах.
        ObjectStat.objects.filter(project_id=obj.pk).update(published=False)

    ProjectObject.objects.filter(
        slug='szhs-zhk-fomenko', title='СЖС ЖК Фоменко',
        summary='24 000 м³ бетона (2024) — непрерывные круглосуточные поставки, стратегический объект региона',
    ).update(summary='ЖК «Фоменко» в Кисловодске.')


class Migration(migrations.Migration):
    dependencies = [('content', '0017_link_mineral_powder_page')]

    operations = [migrations.RunPython(correct_cards, migrations.RunPython.noop)]
