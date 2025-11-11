#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Compiling translations..."
python compile_planned_activations.py || echo "Translation compilation skipped"

echo "Build completed successfully!"
