"""
Fix qso_count for existing ActivationLog records.
Each ActivationLog imported from ADIF represents 1 QSO.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from activations.models import ActivationLog

# Get all logs with qso_count=0
logs_to_fix = ActivationLog.objects.filter(qso_count=0)
count = logs_to_fix.count()

print(f"Found {count} ActivationLog records with qso_count=0")
print("Updating them to qso_count=1...")

# Update all at once
updated = logs_to_fix.update(qso_count=1)

print(f"✓ Updated {updated} records")

# Verify
remaining = ActivationLog.objects.filter(qso_count=0).count()
print(f"\nVerification:")
print(f"  Records with qso_count=0: {remaining}")
print(f"  Total records: {ActivationLog.objects.count()}")

# Recalculate statistics for all users
from accounts.models import UserStatistics

print("\nRecalculating statistics for all users...")
stats_to_update = UserStatistics.objects.all()
for stats in stats_to_update:
    stats.recalculate_from_transactions()
    print(f"  ✓ Updated {stats.user.callsign}")

print("\n✓ All done!")
