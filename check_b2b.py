#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User
from activations.models import ActivationLog

u = User.objects.get(callsign='SUPERADMIN')

print('=== User Stats ===')
print(f'Activator points: {u.statistics.activator_points}')
print(f'Hunter points: {u.statistics.hunter_points}')
print(f'B2B points: {u.statistics.b2b_points}')
print(f'Activator B2B QSO: {u.statistics.activator_b2b_qso}')
print(f'Total B2B QSO: {u.statistics.total_b2b_qso}')

print('\n=== B2B Activation Logs ===')
b2b_logs = ActivationLog.objects.filter(activator=u, is_b2b=True)
print(f'Total B2B logs: {b2b_logs.count()}')
for log in b2b_logs[:5]:
    print(f'  {log.activation_date} - Bunker: {log.bunker.reference_number} - Worked: {log.user.callsign}')
