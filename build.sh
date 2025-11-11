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
python manage.py collectstatic --no-input --verbosity 2
echo ""
echo "=== Verifying static files were collected ==="
echo "Contents of staticfiles directory:"
ls -la staticfiles/ | head -20
echo ""
echo "Checking for images directory:"
ls -la staticfiles/images/ 2>/dev/null || echo "WARNING: No images directory found in staticfiles!"
echo ""
echo "Checking specific files:"
test -f staticfiles/images/bota_logo.png && echo "✓ bota_logo.png found" || echo "✗ bota_logo.png NOT FOUND"
test -f staticfiles/images/favicon.svg && echo "✓ favicon.svg found" || echo "✗ favicon.svg NOT FOUND"

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
