"""
Clear all activation logs and points data from database.
Use this to reset the system before importing new logs.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from activations.models import ActivationLog, LogUpload
from accounts.models import PointsTransaction, PointsTransactionBatch, UserStatistics
from diplomas.models import Diploma, DiplomaProgress
from django.contrib.auth import get_user_model

User = get_user_model()

def clear_all():
    """Clear all logs and points data"""
    
    print("=" * 60)
    print("CLEARING ALL LOGS AND POINTS DATA")
    print("=" * 60)
    
    # 1. Delete all ActivationLogs
    log_count = ActivationLog.objects.count()
    print(f"\n1. Deleting {log_count} ActivationLog records...")
    ActivationLog.objects.all().delete()
    print("   ✓ Done")
    
    # 2. Delete all LogUploads
    upload_count = LogUpload.objects.count()
    print(f"\n2. Deleting {upload_count} LogUpload records...")
    LogUpload.objects.all().delete()
    print("   ✓ Done")
    
    # 3. Delete all PointsTransactions
    tx_count = PointsTransaction.objects.count()
    print(f"\n3. Deleting {tx_count} PointsTransaction records...")
    PointsTransaction.objects.all().delete()
    print("   ✓ Done")
    
    # 4. Delete all PointsTransactionBatches
    batch_count = PointsTransactionBatch.objects.count()
    print(f"\n4. Deleting {batch_count} PointsTransactionBatch records...")
    PointsTransactionBatch.objects.all().delete()
    print("   ✓ Done")
    
    # 5. Reset all UserStatistics to zero
    stats_count = UserStatistics.objects.count()
    print(f"\n5. Resetting {stats_count} UserStatistics records to zero...")
    for stats in UserStatistics.objects.all():
        stats.total_activator_qso = 0
        stats.unique_activations = 0
        stats.activator_b2b_qso = 0
        stats.total_hunter_qso = 0
        stats.unique_bunkers_hunted = 0
        stats.total_b2b_qso = 0
        stats.hunter_points = 0
        stats.activator_points = 0
        stats.b2b_points = 0
        stats.event_points = 0
        stats.diploma_points = 0
        stats.last_transaction_id = 0
        stats.last_recalculated = None
        stats.save()
    print("   ✓ Done")
    
    # 6. Delete all awarded Diplomas
    diploma_count = Diploma.objects.count()
    print(f"\n6. Deleting {diploma_count} awarded Diploma records...")
    Diploma.objects.all().delete()
    print("   ✓ Done")
    
    # 7. Reset all DiplomaProgress
    progress_count = DiplomaProgress.objects.count()
    print(f"\n7. Resetting {progress_count} DiplomaProgress records...")
    for progress in DiplomaProgress.objects.all():
        progress.activated_bunkers_count = 0
        progress.hunted_bunkers_count = 0
        progress.requirements_met = False
        progress.save()
    print("   ✓ Done")
    
    print("\n" + "=" * 60)
    print("DATABASE CLEARED SUCCESSFULLY!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Deleted {log_count} activation logs")
    print(f"  - Deleted {upload_count} log uploads")
    print(f"  - Deleted {tx_count} point transactions")
    print(f"  - Deleted {batch_count} transaction batches")
    print(f"  - Reset {stats_count} user statistics")
    print(f"  - Deleted {diploma_count} awarded diplomas")
    print(f"  - Reset {progress_count} diploma progress records")
    print("\nYou can now upload new logs to test the points system.")
    print("=" * 60)

if __name__ == '__main__':
    import sys
    
    # Safety confirmation
    print("\n⚠️  WARNING: This will DELETE ALL logs, points data, and awarded diplomas!")
    print("This action cannot be undone.\n")
    
    response = input("Are you sure you want to continue? Type 'yes' to confirm: ")
    
    if response.lower() == 'yes':
        clear_all()
    else:
        print("\nOperation cancelled.")
        sys.exit(0)
