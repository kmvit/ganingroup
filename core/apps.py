from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Общие данные, меню и страницы'

    def ready(self):
        from .page_updates import connect_signals

        connect_signals()
