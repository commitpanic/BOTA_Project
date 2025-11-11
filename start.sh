#!/usr/bin/env bash
# Render.com start script
set -o errexit

echo "=== Starting BOTA Application ==="

# Ensure static files exist in the same filesystem as the running app
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Static files collected. Starting Gunicorn..."
exec gunicorn bota_project.wsgi:application
