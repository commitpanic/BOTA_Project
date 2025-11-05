"""
Script to manually update diploma progress for a user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from diplomas.models import DiplomaType, DiplomaProgress, Diploma
from accounts.models import User
from activations.models import ActivationLog
from django.db.models.functions import TruncDate

# Get user
user = User.objects.get(callsign='SP3FCK')
stats = user.statistics

# Calculate total activations = distinct (bunker, date) combinations
total_activations = ActivationLog.objects.filter(
    activator=user
).annotate(
    activation_day=TruncDate('activation_date')
).values('bunker', 'activation_day').distinct().count()

# Calculate unique hunted bunkers
unique_hunted = ActivationLog.objects.filter(
    user=user
).exclude(activator=user).values('bunker').distinct().count()

print(f'User: {user.callsign}')
print(f'Stats: Activator={stats.total_activator_qso}, Hunter={stats.total_hunter_qso}, B2B={stats.activator_b2b_qso}')
print(f'Bunkers: Unique Act={stats.unique_activations}, Total Act Sessions={total_activations} (QSOs={stats.total_activator_qso})')
print(f'         Unique Hunt={unique_hunted}, Total Hunt={unique_hunted}')

# Get active diplomas
active_diplomas = DiplomaType.objects.filter(is_active=True)
print(f'\nActive diplomas: {active_diplomas.count()}')

# Update progress for each diploma type
for dt in active_diplomas:
    progress, created = DiplomaProgress.objects.get_or_create(user=user, diploma_type=dt)
    # Update all progress values from user statistics
    progress.update_points(
        activator=total_activations,
        hunter=stats.total_hunter_qso,
        b2b=stats.activator_b2b_qso,
        unique_activations=stats.unique_activations,
        total_activations=total_activations,
        unique_hunted=unique_hunted,
        total_hunted=unique_hunted
    )
    
    print(f'\n{dt.name_en}:')
    print(f'  Progress: {progress.percentage_complete:.1f}%')
    print(f'  Eligible: {progress.is_eligible}')
    print(f'  Created: {created}')
    
    # Auto-issue diploma if eligible
    if progress.is_eligible:
        diploma, d_created = Diploma.objects.get_or_create(user=user, diploma_type=dt)
        if d_created:
            print(f'  ✅ Diploma issued: {diploma.diploma_number}')
        else:
            print(f'  ℹ️  Diploma already exists: {diploma.diploma_number}')

print('\n=== Summary ===')
diplomas = Diploma.objects.filter(user=user)
print(f'Total diplomas for {user.callsign}: {diplomas.count()}')
for d in diplomas:
    print(f'  - {d.diploma_type.name_en} ({d.diploma_number})')
