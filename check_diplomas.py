#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User
from diplomas.models import Diploma

u = User.objects.get(callsign='SUPERADMIN')
diplomas = Diploma.objects.filter(user=u)

print(f'Total diplomas: {diplomas.count()}')
for d in diplomas:
    print(f'{d.diploma_type.name_en} - {d.diploma_number} - {d.issue_date}')
