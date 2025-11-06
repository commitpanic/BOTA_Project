#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User
from diplomas.models import DiplomaProgress

u = User.objects.get(callsign='SUPERADMIN')

print('=== User Stats ===')
print(f'Activator pts: {u.statistics.activator_points}')
print(f'Hunter pts: {u.statistics.hunter_points}')
print(f'B2B pts: {u.statistics.b2b_points}')
print(f'Unique activated: {u.statistics.unique_activations}')
print(f'Total activator QSOs: {u.statistics.total_activator_qso}')
print(f'Unique hunted: {u.statistics.unique_bunkers_hunted}')

progress = DiplomaProgress.objects.filter(user=u).select_related('diploma_type')
print(f'\n=== Progress Entries ({progress.count()}) ===')
for p in progress:
    print(f'{p.diploma_type.name_en}:')
    print(f'  Progress values: act={p.activator_points} hunt={p.hunter_points} b2b={p.b2b_points}')
    print(f'  Unique: act={p.unique_activations} hunt={p.unique_hunted}')
    print(f'  Requirements: act={p.diploma_type.min_activator_points} hunt={p.diploma_type.min_hunter_points}')
    print(f'  Uniq req: act={p.diploma_type.min_unique_activations} hunt={p.diploma_type.min_unique_hunted}')
    print(f'  Percentage: {p.percentage_complete}% - Eligible: {p.is_eligible}')
    print()
