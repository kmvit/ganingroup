from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone

from calc.models import ConcreteGrade, ConstructionType, DeliveryZone
from content.models import Direction, ObjectPhoto, ObjectStat, ProjectObject, ProjectSupply
from .models import Card, Page, PagePhoto


def remember_previous(sender, instance, using, raw=False, **kwargs):
    if not raw and instance.pk:
        instance._previous_for_lastmod = sender.objects.using(using).filter(pk=instance.pk).first()


def update_page_dates(sender, instance, using, raw=False, signal=None, **kwargs):
    if raw:
        return
    previous = getattr(instance, '_previous_for_lastmod', None) if signal == post_save else None
    fields = [field.attname for field in sender._meta.concrete_fields if not field.primary_key]
    if previous and all(getattr(previous, name) == getattr(instance, name) for name in fields):
        return
    affected = [record for record in (previous, instance) if record is not None]
    now = timezone.now()
    pages = Page.objects.using(using)
    if sender in (Card, PagePhoto):
        pages.filter(pk__in={record.page_id for record in affected if record.published}).update(updated_at=now)
    elif sender in (ProjectSupply, ObjectStat, ObjectPhoto):
        visibility = 'confirmed' if sender is ProjectSupply else 'published'
        ProjectObject.objects.using(using).filter(
            pk__in={record.project_id for record in affected if getattr(record, visibility)},
        ).update(updated_at=now)
    elif sender is Direction and any(record.published for record in affected):
        slugs = ['home', 'produkciya']
        if any(record.published and record.show_in_assets for record in affected):
            slugs.append('o_gruppe')
        pages.filter(slug__in=slugs).update(updated_at=now)
    elif any(getattr(record, 'published', False) for record in affected):
        pages.filter(slug='kalkulyator').update(updated_at=now)


def connect_signals():
    for model in (Card, PagePhoto, ProjectSupply, ObjectStat, ObjectPhoto,
                  Direction, ConcreteGrade, ConstructionType, DeliveryZone):
        pre_save.connect(remember_previous, sender=model)
        post_save.connect(update_page_dates, sender=model)
        post_delete.connect(update_page_dates, sender=model)
