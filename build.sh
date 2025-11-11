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
echo "Installing polib if needed..."
pip install polib
echo "Running compile_translations.py..."
python compile_translations.py || echo "Translation compilation skipped"
echo "Checking compiled .mo files..."
find locale -name "*.mo" -o -name "*.po" | head -20 || echo "No translation files found"

echo ""
echo "=== Build completed successfully! ==="
