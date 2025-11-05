"""
Management command to recalculate user statistics and points
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import User, UserStatistics
from activations.models import ActivationLog


class Command(BaseCommand):
    help = 'Recalculate all user statistics and points from activation logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--callsign',
            type=str,
            help='Recalculate only for specific callsign'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving'
        )

    def handle(self, *args, **options):
        callsign = options.get('callsign')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Get users to process
        if callsign:
            users = User.objects.filter(callsign=callsign)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User {callsign} not found'))
                return
        else:
            users = User.objects.all()
        
        total_users = users.count()
        self.stdout.write(f'Processing {total_users} users...\n')
        
        updated_count = 0
        
        for user in users:
            # Get or create statistics
            stats, created = UserStatistics.objects.get_or_create(user=user)
            
            old_values = {
                'hunter_points': stats.hunter_points,
                'activator_points': stats.activator_points,
                'total_hunter_qso': stats.total_hunter_qso,
                'total_activator_qso': stats.total_activator_qso,
            }
            
            # Recalculate HUNTER statistics (user is in `user` field = person who hunted)
            hunter_qsos = ActivationLog.objects.filter(user=user)
            stats.total_hunter_qso = hunter_qsos.count()
            stats.hunter_points = hunter_qsos.count()  # 1 point per QSO
            stats.unique_bunkers_hunted = hunter_qsos.values('bunker').distinct().count()
            
            # Recalculate ACTIVATOR statistics (user is in `activator` field = person who activated)
            activator_qsos = ActivationLog.objects.filter(activator=user)
            stats.total_activator_qso = activator_qsos.count()
            stats.activator_points = activator_qsos.count()  # 1 point per QSO
            stats.unique_activations = activator_qsos.values('bunker').distinct().count()
            
            # Recalculate B2B statistics
            b2b_qsos = ActivationLog.objects.filter(activator=user, is_b2b=True)
            stats.activator_b2b_qso = b2b_qsos.count()
            stats.total_b2b_qso = b2b_qsos.count()
            stats.b2b_points = b2b_qsos.count()  # 1 point per B2B QSO
            
            # Update total points
            stats.update_total_points()
            
            # Check if anything changed
            changed = False
            changes = []
            for field, old_value in old_values.items():
                new_value = getattr(stats, field)
                if old_value != new_value:
                    changed = True
                    changes.append(f'{field}: {old_value} → {new_value}')
            
            if changed:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {user.callsign}:') + 
                    f' {", ".join(changes)}'
                )
                
                if not dry_run:
                    stats.save()
            else:
                if callsign:  # Only show unchanged for specific user
                    self.stdout.write(
                        self.style.WARNING(f'○ {user.callsign}: No changes needed')
                    )
        
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {updated_count}/{total_users} users')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Updated {updated_count}/{total_users} users')
            )
