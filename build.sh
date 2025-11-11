#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== BOTA Build Script Starting ==="
echo "Python version:"
python --version

echo ""
echo "=== Running Diagnostics ==="
python render_diagnostics.py || echo "Diagnostics failed, continuing anyway..."

echo ""
echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo ""
echo "=== Collecting static files ==="
python manage.py collectstatic --no-input

echo ""
echo "=== Running migrations ==="
python manage.py migrate --no-input

echo ""
echo "=== Compiling translations ==="
python compile_planned_activations.py || echo "Translation compilation skipped"

echo ""
echo "=== Build completed successfully! ==="
