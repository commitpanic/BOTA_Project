#!/usr/bin/env python
"""
Check migration status on production
Run with: python check_migrations.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

print("=" * 60)
print("BOTA Project - Migration Status Check")
print("=" * 60)

# Check database connection
print("\n1. Database Connection:")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✓ Connected to: {version}")
except Exception as e:
    print(f"   ✗ Connection failed: {e}")

# Check if tables exist
print("\n2. Critical Tables:")
tables_to_check = [
    'cluster_spot',
    'cluster_cluster',
    'cluster_spothistory',
    'diplomas_diploma',
    'diplomas_diplomatype',
    'diplomas_diplomaprogress',
    'bunkers_bunker',
    'accounts_user',
    'activations_activationlog'
]

with connection.cursor() as cursor:
    for table in tables_to_check:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table}'
            );
        """)
        exists = cursor.fetchone()[0]
        status = "✓" if exists else "✗"
        print(f"   {status} {table}")

# Show migration status
print("\n3. Migration Status:")
os.system('python manage.py showmigrations')

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
