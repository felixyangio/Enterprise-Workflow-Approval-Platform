#!/bin/sh
set -e

mkdir -p /app/data /app/media /app/staticfiles

if [ ! -f /app/db.sqlite3 ]; then
  if [ -f /app/data/db.sqlite3 ]; then
    ln -s /app/data/db.sqlite3 /app/db.sqlite3
  else
    touch /app/data/db.sqlite3
    ln -s /app/data/db.sqlite3 /app/db.sqlite3
  fi
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "$DJANGO_SEED_DEMO_DATA" = "True" ] || [ "$DJANGO_SEED_DEMO_DATA" = "true" ]; then
  python manage.py seed_workflow
fi

exec gunicorn oa.wsgi:application --bind 0.0.0.0:${BACKEND_PORT:-8000} --workers 3 --timeout 120
