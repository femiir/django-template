#!/bin/sh
set -e

echo "starting migrations..."
python manage.py makemigrations --noinput #--skip-checks
echo "applying migrations..."
python manage.py migrate --noinput #--skip-checks

echo "collecting static files..."
python manage.py collectstatic --noinput

echo "starting the application..."

# echo "starting server..."
# uvicorn config.asgi:application

# echo "starting debugpy..."
python -X frozen_modules=off -m debugpy --listen 0.0.0.0:5678 -m daphne -b 0.0.0.0 -p 8000 config.asgi:application