"""
Management command to migrate existing UserStatistics to PointsTransaction system.

This creates historical PointsTransaction records based on existing ActivationLog data,
establishing an audit trail for all past point awards.

Usage:
    python manage.py migrate_to_points_transactions [--dry-run] [--user CALLSIGN]
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import UserStatistics, PointsTransaction, PointsTransactionBatch
from accounts.points_service import PointsService
from activations.models import ActivationLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate existing UserStatistics to PointsTransaction audit trail system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making changes'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Migrate only specific user (by callsign)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if transactions already exist'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_callsign = options.get('user')
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get users to migrate
        if user_callsign:
            try:
                users = [User.objects.get(callsign=user_callsign)]
                self.stdout.write(f'Migrating single user: {user_callsign}')
            except User.DoesNotExist:
                raise CommandError(f'User with callsign "{user_callsign}" not found')
        else:
            users = User.objects.all()
            self.stdout.write(f'Migrating all users ({users.count()} total)')

        total_users = 0
        total_transactions = 0
        skipped_users = 0
        errors = []

        for user in users:
            try:
                result = self._migrate_user(user, dry_run, force)
                if result['migrated']:
                    total_users += 1
                    total_transactions += result['transactions_created']
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {user.callsign}: Created {result["transactions_created"]} transactions'
                        )
                    )
                else:
                    skipped_users += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⊘ {user.callsign}: {result["reason"]}'
                        )
                    )
            except Exception as e:
                errors.append(f'{user.callsign}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'✗ {user.callsign}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Migration Complete!'))
        self.stdout.write(f'Users migrated: {total_users}')
        self.stdout.write(f'Users skipped: {skipped_users}')
        self.stdout.write(f'Total transactions created: {total_transactions}')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))

        if dry_run:
            self.stdout.write('\n' + self.style.WARNING('DRY RUN - No changes were saved'))

    @transaction.atomic
    def _migrate_user(self, user, dry_run=False, force=False):
        """
        Migrate a single user's data to PointsTransaction system.
        
        Returns:
            dict: Migration result with keys 'migrated', 'transactions_created', 'reason'
        """
        # Check if user already has transactions
        existing_count = PointsTransaction.objects.filter(user=user).count()
        if existing_count > 0 and not force:
            return {
                'migrated': False,
                'transactions_created': 0,
                'reason': f'Already has {existing_count} transactions (use --force to override)'
            }

        # Get all activation logs for this user
        activator_logs = ActivationLog.objects.filter(activator=user).select_related('user', 'bunker')
        hunter_logs = ActivationLog.objects.filter(user=user).exclude(activator=user).select_related('activator', 'bunker')

        transactions_created = 0

        if dry_run:
            # Just count what would be created
            transactions_created = activator_logs.count() + hunter_logs.count()
            # Check for B2B
            b2b_logs = activator_logs.filter(is_b2b=True, b2b_confirmed=True)
            transactions_created += b2b_logs.count()
            
            return {
                'migrated': True,
                'transactions_created': transactions_created,
                'reason': 'Dry run'
            }

        # Create a migration batch
        batch = PointsTransactionBatch.objects.create(
            name=f'Historical migration for {user.callsign}',
            description=f'Migrated from existing ActivationLog data on {timezone.now().strftime("%Y-%m-%d %H:%M")}',
            created_by=None  # System migration
        )

        created_transactions = []

        # Migrate activator points
        for log in activator_logs:
            # Skip if already has transaction
            if log.points_transaction:
                continue

            tx = PointsTransaction.objects.create(
                user=user,
                transaction_type=PointsTransaction.ACTIVATOR_QSO,
                activator_points=1,
                activation_log=log,
                bunker=log.bunker,
                reason='Historical migration from ActivationLog',
                notes=f'QSO with {log.user.callsign} on {log.activation_date.strftime("%Y-%m-%d")}',
                created_by=None
            )
            
            # Link transaction to log
            log.points_transaction = tx
            log.points_awarded = True
            log.save(update_fields=['points_transaction', 'points_awarded'])
            
            created_transactions.append(tx)
            transactions_created += 1

        # Migrate hunter points
        for log in hunter_logs:
            # Check if activator already created a transaction for this
            # (we create one transaction per QSO, viewable by both parties)
            if log.points_transaction:
                continue

            tx = PointsTransaction.objects.create(
                user=user,
                transaction_type=PointsTransaction.HUNTER_QSO,
                hunter_points=1,
                activation_log=log,
                bunker=log.bunker,
                reason='Historical migration from ActivationLog',
                notes=f'Worked {log.activator.callsign} at {log.bunker.reference_number}',
                created_by=None
            )
            
            created_transactions.append(tx)
            transactions_created += 1

        # Migrate B2B points (only for confirmed B2B)
        b2b_logs = activator_logs.filter(is_b2b=True, b2b_confirmed=True)
        for log in b2b_logs:
            # Check if B2B transaction already exists
            existing_b2b = PointsTransaction.objects.filter(
                user=user,
                activation_log=log,
                transaction_type=PointsTransaction.B2B_CONFIRMED
            ).exists()
            
            if existing_b2b:
                continue

            tx = PointsTransaction.objects.create(
                user=user,
                transaction_type=PointsTransaction.B2B_CONFIRMED,
                b2b_points=1,
                activation_log=log,
                bunker=log.bunker,
                reason='Historical migration - confirmed B2B',
                notes=f'B2B with {log.b2b_partner.callsign if log.b2b_partner else "unknown"}',
                created_by=None
            )
            
            created_transactions.append(tx)
            transactions_created += 1

        # Add all transactions to batch
        batch.transactions.set(created_transactions)

        # Recalculate user statistics from transactions
        try:
            stats = UserStatistics.objects.get(user=user)
            stats.recalculate_from_transactions()
        except UserStatistics.DoesNotExist:
            # Create statistics if doesn't exist
            stats = UserStatistics.objects.create(user=user)
            stats.recalculate_from_transactions()

        return {
            'migrated': True,
            'transactions_created': transactions_created,
            'reason': 'Success'
        }
