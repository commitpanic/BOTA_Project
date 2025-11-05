#!/usr/bin/env python
"""
Update existing auto-created users to set auto_created=True
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User

# Update users with temporary email to mark as auto-created
count = User.objects.filter(email__endswith='@temp.bota.invalid').update(auto_created=True)
print(f'Updated {count} auto-created users')

# Show summary
total_users = User.objects.count()
auto_created = User.objects.filter(auto_created=True).count()
registered = total_users - auto_created

print(f'\nUser Summary:')
print(f'  Total users: {total_users}')
print(f'  Auto-created (inactive): {auto_created}')
print(f'  Registered (active): {registered}')
