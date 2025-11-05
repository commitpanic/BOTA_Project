"""
Management command to update diploma progress for all users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from diplomas.models import DiplomaType, DiplomaProgress, Diploma
from accounts.models import UserStatistics

User = get_user_model()


class Command(BaseCommand):
    help = 'Update diploma progress for all users and auto-award eligible diplomas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update only for specific user (callsign)',
        )

    def handle(self, *args, **options):
        user_filter = options.get('user')
        
        if user_filter:
            users = User.objects.filter(callsign=user_filter)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User {user_filter} not found'))
                return
        else:
            users = User.objects.filter(is_active=True)
        
        self.stdout.write(f'Updating diploma progress for {users.count()} users...')
        
        # Get all active diplomas
        active_diplomas = DiplomaType.objects.filter(is_active=True)
        self.stdout.write(f'Found {active_diplomas.count()} active diploma types')
        
        diplomas_awarded = 0
        progress_updated = 0
        
        for user in users:
            from activations.models import ActivationLog
            from django.db.models.functions import TruncDate
            
            # Get user statistics
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            
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
            
            self.stdout.write(f'\nUser: {user.callsign}')
            self.stdout.write(f'  Activator QSOs: {stats.total_activator_qso}')
            self.stdout.write(f'  Activation Sessions: {total_activations}')
            self.stdout.write(f'  Hunter QSOs: {stats.total_hunter_qso}')
            self.stdout.write(f'  B2B QSOs: {stats.activator_b2b_qso}')
            
            for diploma_type in active_diplomas:
                # Skip time-limited diplomas that are not currently valid
                if diploma_type.is_time_limited() and not diploma_type.is_currently_valid():
                    continue
                
                # Get or create progress record
                progress, created = DiplomaProgress.objects.get_or_create(
                    user=user,
                    diploma_type=diploma_type
                )
                
                if created:
                    self.stdout.write(f'  Created progress for: {diploma_type.name_en}')
                
                # Update points and bunker counts
                progress.update_points(
                    activator=total_activations,
                    hunter=stats.total_hunter_qso,
                    b2b=stats.activator_b2b_qso,
                    unique_activations=stats.unique_activations,
                    total_activations=total_activations,
                    unique_hunted=unique_hunted,
                    total_hunted=unique_hunted
                )
                progress_updated += 1
                
                self.stdout.write(
                    f'  {diploma_type.name_en}: '
                    f'ACT:{progress.activator_points}/{diploma_type.min_activator_points} '
                    f'HNT:{progress.hunter_points}/{diploma_type.min_hunter_points} '
                    f'B2B:{progress.b2b_points}/{diploma_type.min_b2b_points} '
                    f'({progress.percentage_complete}% - {"ELIGIBLE" if progress.is_eligible else "not eligible"})'
                )
                
                # Check if eligible and not already awarded
                if progress.is_eligible:
                    existing = Diploma.objects.filter(
                        user=user,
                        diploma_type=diploma_type
                    ).exists()
                    
                    if not existing:
                        # Award diploma
                        diploma = Diploma.objects.create(
                            diploma_type=diploma_type,
                            user=user,
                            activator_points_earned=progress.activator_points,
                            hunter_points_earned=progress.hunter_points,
                            b2b_points_earned=progress.b2b_points
                        )
                        diplomas_awarded += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ AWARDED: {diploma_type.name_en} (#{diploma.diploma_number})'
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nCompleted! Updated {progress_updated} progress records, '
                f'awarded {diplomas_awarded} diplomas'
            )
        )
