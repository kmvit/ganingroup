from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0008_page_updated_at')]

    operations = [
        migrations.AddField(
            model_name='page', name='video_url',
            field=models.URLField(blank=True, help_text='Для страницы «Минеральный порошок»: вставьте ссылку на видео в Google Drive.', verbose_name='Ссылка на видео'),
        ),
    ]
