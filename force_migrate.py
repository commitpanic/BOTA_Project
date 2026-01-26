#!/usr/bin/env python
"""
Force run all migrations on production
Run with: python force_migrate.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

print("=" * 60)
print("FORCE MIGRATE - Running all pending migrations")
print("=" * 60)

# Check database connection
print("\n1. Testing database connection...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✓ Connected to: {version}")
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    sys.exit(1)

# Show current migration status
print("\n2. Current migration status:")
call_command('showmigrations', '--list')

# Run migrations
print("\n3. Running migrations...")
try:
    call_command('migrate', '--verbosity=2', '--no-input')
    print("   ✓ Migrations completed successfully!")
except Exception as e:
    print(f"   ✗ Migration failed: {e}")
    sys.exit(1)

# Show final status
print("\n4. Final migration status:")
call_command('showmigrations', '--list')

# Verify info_url column exists
print("\n5. Verifying bunkers_bunker.info_url column...")
try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='bunkers_bunker' AND column_name='info_url';
        """)
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Column exists: {result[0]}")
        else:
            print(f"   ✗ Column does NOT exist!")
except Exception as e:
    print(f"   ✗ Check failed: {e}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
