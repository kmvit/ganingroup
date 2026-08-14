#!/bin/sh
# Старт контейнера: миграции, статика, первичный контент — затем gunicorn.
set -e

echo "→ миграции"
python manage.py migrate --noinput

echo "→ сборка статики"
python manage.py collectstatic --noinput --clear >/dev/null

# Контент заливается ТОЛЬКО в пустую базу: иначе удалённые заказчиком
# записи возвращались бы при каждом перезапуске.
echo "→ первичный контент (если база пустая)"
python manage.py seed_content --if-empty

echo "→ запуск gunicorn"
exec gunicorn ganin_site.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
