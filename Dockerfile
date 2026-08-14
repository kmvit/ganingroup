# Сайт ГАНИН ГРУПП — образ приложения (gunicorn).
# Статика собирается при старте в /app/staticfiles, база и медиа живут
# на хосте через bind-mount, поэтому пересборка образа не трогает контент.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DB_PATH=/app/data/db.sqlite3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x deploy/entrypoint.sh && mkdir -p /app/data /app/media /app/staticfiles

EXPOSE 8000
ENTRYPOINT ["deploy/entrypoint.sh"]
