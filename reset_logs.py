#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User
from activations.models import ActivationLog

# Get users
superadmin = User.objects.get(callsign='SUPERADMIN')
sp3jfb = User.objects.get(callsign='SP3JFB')

print('=== Deleting old logs ===')

# Delete all logs for both users
superadmin_logs = ActivationLog.objects.filter(activator=superadmin)
print(f'SUPERADMIN logs: {superadmin_logs.count()}')
superadmin_logs.delete()

sp3jfb_logs = ActivationLog.objects.filter(activator=sp3jfb)
print(f'SP3JFB logs: {sp3jfb_logs.count()}')
sp3jfb_logs.delete()

# Reset statistics
superadmin.statistics.activator_points = 0
superadmin.statistics.hunter_points = 0
superadmin.statistics.b2b_points = 0
superadmin.statistics.activator_b2b_qso = 0
superadmin.statistics.total_b2b_qso = 0
superadmin.statistics.total_activator_qso = 0
superadmin.statistics.total_hunter_qso = 0
superadmin.statistics.unique_activations = 0
superadmin.statistics.unique_bunkers_hunted = 0
superadmin.statistics.save()

sp3jfb.statistics.activator_points = 0
sp3jfb.statistics.hunter_points = 0
sp3jfb.statistics.b2b_points = 0
sp3jfb.statistics.activator_b2b_qso = 0
sp3jfb.statistics.total_b2b_qso = 0
sp3jfb.statistics.total_activator_qso = 0
sp3jfb.statistics.total_hunter_qso = 0
sp3jfb.statistics.unique_activations = 0
sp3jfb.statistics.unique_bunkers_hunted = 0
sp3jfb.statistics.save()

print('Logs deleted and statistics reset')
