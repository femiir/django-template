#!/bin/sh
set -e

echo "starting migrations..."
python manage.py migrate --noinput #--skip-checks

# echo "starting the server..."
# python manage.py runserver 0.0.0.0:8000
echo "starting debugpy..."
python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:80
