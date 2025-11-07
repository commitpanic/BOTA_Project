"""
Tests for PointsService - business logic for awarding and managing points.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from accounts.models import (
    PointsTransaction, PointsTransactionBatch, UserStatistics
)
from accounts.points_service import PointsService
from activations.models import ActivationLog, LogUpload
from bunkers.models import Bunker, BunkerCategory


User = get_user_model()


class PointsServiceTestCase(TestCase):
    """Test suite for PointsService business logic."""
    
    def setUp(self):
        """Create test data."""
        # Create test users
        self.activator = User.objects.create_user(
            email='activator@test.com',
            callsign='SP1ACT',
            password='test123'
        )
        self.hunter1 = User.objects.create_user(
            email='hunter1@test.com',
            callsign='SP1HNT',
            password='test123'
        )
        self.hunter2 = User.objects.create_user(
            email='hunter2@test.com',
            callsign='SP2HNT',
            password='test123'
        )
        
        # Create bunker category
        self.category = BunkerCategory.objects.create(
            name_pl='Testowa Kategoria',
            name_en='Test Category'
        )
        
        # Create test bunker
        self.bunker = Bunker.objects.create(
            reference_number='BOTA-TEST-001',
            name_pl='Testowy Bunkier',
            name_en='Test Bunker',
            category=self.category,
            latitude=Decimal('52.2297'),
            longitude=Decimal('21.0122')
        )
        
        # Create log upload
        self.log_upload = LogUpload.objects.create(
            user=self.activator,
            file_checksum='abc123def456',
            filename='test.adi'
        )
    
    def test_award_activator_points_basic(self):
        """Test awarding basic activator points for QSO."""
        # Create activation log
        log = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Award points
        transaction = PointsService.award_activator_points(
            user=self.activator,
            activation_log=log,
            created_by=self.activator
        )
        
        # Verify transaction created
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, PointsTransaction.ACTIVATOR_QSO)
        self.assertEqual(transaction.activator_points, 1)
        self.assertEqual(transaction.total_points, 1)
        self.assertEqual(transaction.user, self.activator)
        self.assertEqual(transaction.activation_log, log)
        
        # Verify log marked as processed
        log.refresh_from_db()
        self.assertTrue(log.points_awarded)
        self.assertEqual(log.points_transaction, transaction)
        
        # Verify statistics updated
        stats = UserStatistics.objects.get(user=self.activator)
        self.assertEqual(stats.activator_points, 1)
        self.assertEqual(stats.total_points, 1)
        self.assertEqual(stats.last_transaction_id, transaction.id)
    
    def test_award_activator_points_idempotent(self):
        """Test that awarding points twice for same log doesn't duplicate."""
        log = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Award points first time
        tx1 = PointsService.award_activator_points(
            user=self.activator,
            activation_log=log
        )
        
        # Try to award again - should return None
        tx2 = PointsService.award_activator_points(
            user=self.activator,
            activation_log=log
        )
        
        self.assertIsNotNone(tx1)
        self.assertIsNone(tx2)
        
        # Verify only 1 point awarded
        stats = UserStatistics.objects.get(user=self.activator)
        self.assertEqual(stats.activator_points, 1)
        
        # Verify only 1 transaction exists
        count = PointsTransaction.objects.filter(
            user=self.activator,
            activation_log=log
        ).count()
        self.assertEqual(count, 1)
    
    def test_award_hunter_points_basic(self):
        """Test awarding hunter points for QSO."""
        log = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Award points
        transaction = PointsService.award_hunter_points(
            user=self.hunter1,
            activation_log=log
        )
        
        # Verify transaction
        self.assertEqual(transaction.transaction_type, PointsTransaction.HUNTER_QSO)
        self.assertEqual(transaction.hunter_points, 1)
        self.assertEqual(transaction.total_points, 1)
        self.assertEqual(transaction.user, self.hunter1)
        
        # Verify statistics
        stats = UserStatistics.objects.get(user=self.hunter1)
        self.assertEqual(stats.hunter_points, 1)
        self.assertEqual(stats.total_points, 1)
    
    def test_confirm_b2b_success(self):
        """Test B2B confirmation when both logs uploaded."""
        # Log 1: hunter1 activates, hunter2 works him
        log1 = ActivationLog.objects.create(
            activator=self.hunter1,
            user=self.hunter2,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Log 2: hunter2 activates, hunter1 works him (reciprocal)
        log2 = ActivationLog.objects.create(
            activator=self.hunter2,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Confirm B2B
        tx1, tx2 = PointsService.confirm_b2b(
            log1=log1,
            log2=log2,
            created_by=self.activator
        )
        
        # Verify transactions created
        self.assertIsNotNone(tx1)
        self.assertIsNotNone(tx2)
        
        self.assertEqual(tx1.transaction_type, PointsTransaction.B2B_CONFIRMED)
        self.assertEqual(tx1.b2b_points, 1)
        self.assertEqual(tx1.user, self.hunter1)
        
        self.assertEqual(tx2.transaction_type, PointsTransaction.B2B_CONFIRMED)
        self.assertEqual(tx2.b2b_points, 1)
        self.assertEqual(tx2.user, self.hunter2)
        
        # Verify logs marked as B2B
        log1.refresh_from_db()
        log2.refresh_from_db()
        
        self.assertTrue(log1.b2b_confirmed)
        self.assertTrue(log2.b2b_confirmed)
        self.assertEqual(log1.b2b_partner, self.hunter2)
        self.assertEqual(log2.b2b_partner, self.hunter1)
        self.assertEqual(log1.b2b_partner_log, log2)
        self.assertEqual(log2.b2b_partner_log, log1)
        
        # Verify statistics
        stats1 = UserStatistics.objects.get(user=self.hunter1)
        stats2 = UserStatistics.objects.get(user=self.hunter2)
        
        self.assertEqual(stats1.b2b_points, 1)
        self.assertEqual(stats2.b2b_points, 1)
    
    def test_confirm_b2b_already_confirmed(self):
        """Test that confirming B2B twice doesn't duplicate points."""
        log1 = ActivationLog.objects.create(
            activator=self.hunter1,
            user=self.hunter2,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        log2 = ActivationLog.objects.create(
            activator=self.hunter2,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Confirm first time
        tx1, tx2 = PointsService.confirm_b2b(log1, log2)
        self.assertIsNotNone(tx1)
        
        # Try again - should return (None, None)
        result = PointsService.confirm_b2b(log1, log2)
        self.assertEqual(result, (None, None))
        
        # Verify only 1 point each
        stats1 = UserStatistics.objects.get(user=self.hunter1)
        stats2 = UserStatistics.objects.get(user=self.hunter2)
        
        self.assertEqual(stats1.b2b_points, 1)
        self.assertEqual(stats2.b2b_points, 1)
    
    def test_confirm_b2b_different_bunkers_fails(self):
        """Test B2B confirmation fails if bunkers don't match."""
        bunker2 = Bunker.objects.create(
            reference_number='BOTA-TEST-002',
            name_pl='Testowy Bunkier 2',
            name_en='Test Bunker 2',
            category=self.category,
            latitude=Decimal('52.2297'),
            longitude=Decimal('21.0122')
        )
        
        log1 = ActivationLog.objects.create(
            activator=self.hunter1,
            user=self.hunter2,
            bunker=self.bunker,  # Different bunker
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        log2 = ActivationLog.objects.create(
            activator=self.hunter2,
            user=self.hunter1,
            bunker=bunker2,  # Different bunker
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        result = PointsService.confirm_b2b(log1, log2)
        self.assertEqual(result, (None, None))  # Should fail - different bunkers
    
    
    # TODO: Implement time_window validation in confirm_b2b if needed
    # def test_confirm_b2b_time_window_validation(self):
    
    def test_cancel_b2b(self):
        """Test canceling B2B points."""
        log1 = ActivationLog.objects.create(
            activator=self.hunter1,
            user=self.hunter2,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        log2 = ActivationLog.objects.create(
            activator=self.hunter2,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Confirm B2B
        tx1, tx2 = PointsService.confirm_b2b(log1, log2)
        
        # Verify points awarded
        stats1 = UserStatistics.objects.get(user=self.hunter1)
        stats2 = UserStatistics.objects.get(user=self.hunter2)
        self.assertEqual(stats1.b2b_points, 1)
        self.assertEqual(stats2.b2b_points, 1)
        
        # Cancel B2B (only need to pass one log - it finds partner)
        reversal_tx1, reversal_tx2 = PointsService.cancel_b2b(
            log=log1,
            reason='Test cancellation',
            created_by=self.activator
        )
        
        # Verify reversal transactions created
        self.assertIsNotNone(reversal_tx1)
        self.assertIsNotNone(reversal_tx2)
        
        self.assertEqual(reversal_tx1.transaction_type, PointsTransaction.REVERSAL)
        self.assertEqual(reversal_tx1.b2b_points, -1)  # Negative!
        
        # Verify logs unmarked
        log1.refresh_from_db()
        log2.refresh_from_db()
        
        self.assertFalse(log1.b2b_confirmed)
        self.assertFalse(log2.b2b_confirmed)
        # Note: cancel_b2b doesn't clear b2b_partner, only b2b_confirmed
        
        # Verify statistics back to zero
        stats1.refresh_from_db()
        stats2.refresh_from_db()
        
        self.assertEqual(stats1.b2b_points, 0)
        self.assertEqual(stats2.b2b_points, 0)
    
    def test_transaction_reversal(self):
        """Test reversing a transaction."""
        log = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Award points
        transaction = PointsService.award_activator_points(
            user=self.activator,
            activation_log=log
        )
        
        # Verify points awarded
        stats = UserStatistics.objects.get(user=self.activator)
        self.assertEqual(stats.activator_points, 1)
        
        # Reverse transaction
        reversal = transaction.reverse(reason='Test reversal')
        
        # Verify reversal created
        self.assertIsNotNone(reversal)
        self.assertEqual(reversal.transaction_type, PointsTransaction.REVERSAL)
        self.assertEqual(reversal.activator_points, -1)  # Negative
        self.assertEqual(reversal.reverses, transaction)
        
        # Verify statistics updated
        stats.refresh_from_db()
        self.assertEqual(stats.activator_points, 0)
    
    def test_create_batch(self):
        """Test creating transaction batch."""
        # Create multiple logs with different times to avoid unique constraint
        logs = []
        now = timezone.now()
        for i in range(3):
            log = ActivationLog.objects.create(
                activator=self.activator,
                user=self.hunter1,
                bunker=self.bunker,
                activation_date=now + timedelta(minutes=i),  # Different times
                band='20m',
                mode='SSB',
                log_upload=self.log_upload
            )
            logs.append(log)
        
        # Award points for all
        transactions = []
        for log in logs:
            tx = PointsService.award_activator_points(
                user=self.activator,
                activation_log=log
            )
            transactions.append(tx)
        
        # Create batch (name is first param, not description)
        batch = PointsService.create_batch(
            name='Test batch import',
            transactions=transactions,
            log_upload=self.log_upload
        )
        
        # Verify batch created
        self.assertIsNotNone(batch)
        self.assertEqual(batch.transactions.count(), 3)  # ManyToMany count
        self.assertEqual(batch.log_upload, self.log_upload)
        
        # Verify transactions linked to batch
        for tx in transactions:
            self.assertIn(batch, tx.batches.all())
    
    def test_recalculate_from_transactions(self):
        """Test recalculating statistics from transaction history."""
        # Create various transactions with different times
        now = timezone.now()
        log1 = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=now,
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        log2 = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter2,
            bunker=self.bunker,
            activation_date=now + timedelta(minutes=1),  # Different time
            band='40m',
            mode='CW',
            log_upload=self.log_upload
        )
        
        # Award activator points
        PointsService.award_activator_points(self.activator, log1)
        PointsService.award_activator_points(self.activator, log2)
        
        # Award hunter points
        PointsService.award_hunter_points(self.hunter1, log1)
        
        # Verify initial stats
        stats = UserStatistics.objects.get(user=self.activator)
        self.assertEqual(stats.activator_points, 2)
        self.assertEqual(stats.total_points, 2)
        
        # Manually corrupt statistics
        stats.activator_points = 999
        stats.total_points = 999
        stats.save()
        
        # Recalculate
        stats.recalculate_from_transactions()
        
        # Verify corrected
        self.assertEqual(stats.activator_points, 2)
        self.assertEqual(stats.total_points, 2)
        self.assertIsNotNone(stats.last_recalculated)
    
    def test_statistics_cache_consistency(self):
        """Test that UserStatistics cache stays consistent with transactions."""
        log = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=timezone.now(),
            band='20m',
            mode='SSB',
            log_upload=self.log_upload
        )
        
        # Award points
        tx = PointsService.award_activator_points(self.activator, log)
        
        # Get stats from cache
        stats = UserStatistics.objects.get(user=self.activator)
        cached_points = stats.total_points
        
        # Recalculate from transactions
        stats.recalculate_from_transactions()
        recalculated_points = stats.total_points
        
        # Should match
        self.assertEqual(cached_points, recalculated_points)
        self.assertEqual(stats.last_transaction_id, tx.id)
