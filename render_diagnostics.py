#!/usr/bin/env python
"""
Diagnostic script to check Render environment configuration
"""
import os
import sys

print("=" * 60)
print("BOTA RENDER DIAGNOSTICS")
print("=" * 60)

# Check Python version
print(f"\nPython version: {sys.version}")

# Check environment variables
env_vars = [
    'SECRET_KEY',
    'DEBUG',
    'ALLOWED_HOSTS',
    'DATABASE_URL',
    'RENDER',
    'RENDER_EXTERNAL_HOSTNAME',
    'PORT',
]

print("\nEnvironment Variables:")
print("-" * 60)
for var in env_vars:
    value = os.environ.get(var)
    if var == 'SECRET_KEY' and value:
        print(f"  {var}: ***HIDDEN*** (length: {len(value)})")
    elif var == 'DATABASE_URL' and value:
        # Show only the database name
        if '@' in value and '/' in value:
            db_name = value.split('/')[-1]
            print(f"  {var}: ***HIDDEN*** (database: {db_name})")
        else:
            print(f"  {var}: ***HIDDEN***")
    else:
        print(f"  {var}: {value}")

# Check if we can import Django
print("\n" + "-" * 60)
try:
    import django
    print(f"✓ Django imported successfully (version {django.get_version()})")
except Exception as e:
    print(f"✗ Django import failed: {e}")

# Check database connection
print("\n" + "-" * 60)
print("Testing database connection...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
    django.setup()
    
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result:
            print("✓ Database connection successful!")
        else:
            print("✗ Database connection failed - no result")
except Exception as e:
    print(f"✗ Database connection failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTICS COMPLETE")
print("=" * 60)
