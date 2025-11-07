import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User
from activations.models import ActivationLog

# Get SP3FCK user
sp3fck = User.objects.get(callsign='SP3FCK')
stats = sp3fck.statistics

print(f"SP3FCK Statistics:")
print(f"  Activator B2B QSO: {stats.activator_b2b_qso}")
print(f"  Total B2B QSO: {stats.total_b2b_qso}")
print(f"  B2B Points: {stats.b2b_points}")
print()

# Check actual B2B logs
b2b_logs = ActivationLog.objects.filter(
    activator=sp3fck,
    is_b2b=True
)

print(f"B2B Activation Logs (as activator): {b2b_logs.count()}")
for log in b2b_logs:
    print(f"  - {log.activation_date.date()} at {log.bunker.reference_number} ({log.bunker.name_en})")
    print(f"    Mode: {log.mode}, Band: {log.band}, QSO Count: {log.qso_count}")

print("\nAll SP3FCK activations grouped by bunker:")
from django.db.models import Count, Sum
activations = ActivationLog.objects.filter(
    activator=sp3fck
).values(
    'bunker__reference_number',
    'bunker__name_en'
).annotate(
    activation_count=Count('id'),
    total_qso=Sum('qso_count'),
    b2b_count=Count('id', filter=django.db.models.Q(is_b2b=True))
).order_by('-activation_count')

for act in activations:
    print(f"  {act['bunker__reference_number']}: {act['activation_count']} activations, {act['total_qso']} QSOs, {act['b2b_count']} B2B")
