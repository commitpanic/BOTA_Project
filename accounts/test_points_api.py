"""
Tests for Points Transaction API endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from accounts.models import PointsTransaction, PointsTransactionBatch, UserStatistics
from accounts.points_service import PointsService
from bunkers.models import Bunker, BunkerCategory
from activations.models import ActivationLog

User = get_user_model()


class PointsTransactionAPITest(TestCase):
    """Test Points Transaction API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            callsign='SP1ADMIN',
            password='adminpass123'
        )
        
        # Create bunker category and bunker
        self.category = BunkerCategory.objects.create(
            name_pl='Test Category',
            name_en='Test Category'
        )
        self.bunker = Bunker.objects.create(
            reference_number='SP-0001',
            name_en='Test Bunker',
            name_pl='Testowy Bunkier',
            category=self.category,
            latitude=Decimal('52.192798'),
            longitude=Decimal('15.425792')
        )
        
        # Create some transactions
        # Need activation logs for transactions
        self.activation_log1 = ActivationLog.objects.create(
            user=self.user,
            activator=self.user,
            bunker=self.bunker,
            activation_date=timezone.now(),
            mode='SSB'
        )
        
        self.activation_log2 = ActivationLog.objects.create(
            user=self.user,
            activator=self.admin,  # Different activator, so user gets hunter points
            bunker=self.bunker,
            activation_date=timezone.now(),
            mode='CW'
        )
        
        self.tx1 = PointsService.award_activator_points(
            user=self.user,
            activation_log=self.activation_log1,
            created_by=self.admin
        )
        
        self.tx2 = PointsService.award_hunter_points(
            user=self.user,
            activation_log=self.activation_log2,
            created_by=self.admin
        )
    
    def test_list_transactions_anonymous(self):
        """Anonymous users can list transactions"""
        url = reverse('pointstransaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_list_transactions_authenticated(self):
        """Authenticated users can list transactions"""
        self.client.force_authenticate(user=self.user)
        url = reverse('pointstransaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_transaction(self):
        """Can retrieve single transaction"""
        url = reverse('pointstransaction-detail', args=[self.tx1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.tx1.id)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['transaction_type'], 'activator_qso')  # Lowercase from DB
    
    def test_filter_by_user(self):
        """Can filter transactions by user"""
        url = reverse('pointstransaction-list')
        response = self.client.get(url, {'user': self.user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should be for this user
        for tx in response.data['results']:
            self.assertEqual(tx['user'], self.user.id)
    
    def test_filter_by_transaction_type(self):
        """Can filter by transaction type"""
        url = reverse('pointstransaction-list')
        response = self.client.get(url, {'transaction_type': 'activator_qso'})  # Lowercase
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should be activator_qso
        for tx in response.data['results']:
            self.assertEqual(tx['transaction_type'], 'activator_qso')
    
    def test_user_history_endpoint(self):
        """Test user history custom endpoint"""
        url = f'/api/points-transactions/user/{self.user.id}/history/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertIn('total_transactions', response.data)
        self.assertIn('totals', response.data)
        self.assertIn('transactions', response.data)
        
        # Verify totals
        totals = response.data['totals']
        self.assertIsNotNone(totals['total_points'])
        self.assertGreater(totals['activator_points'], 0)
        self.assertGreater(totals['hunter_points'], 0)
    
    def test_recalculate_points_requires_admin(self):
        """Recalculate endpoint requires admin permissions"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userstatistics-recalculate', args=[self.user.statistics.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_recalculate_points_as_admin(self):
        """Admin can recalculate user points"""
        self.client.force_authenticate(user=self.admin)
        
        # Manually mess up the stats
        stats = self.user.statistics
        stats.activator_points = 999
        stats.save()
        
        # Recalculate
        url = reverse('userstatistics-recalculate', args=[stats.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('statistics', response.data)
        
        # Verify points were recalculated correctly
        stats.refresh_from_db()
        self.assertNotEqual(stats.activator_points, 999)
        self.assertEqual(stats.activator_points, 1)  # 1 point from tx1
    
    def test_cannot_create_transaction_via_api(self):
        """Cannot create transactions via API (read-only)"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('pointstransaction-list')
        data = {
            'user': self.user.id,
            'transaction_type': 'ACTIVATOR_QSO',
            'activator_points': 10
        }
        response = self.client.post(url, data)
        
        # Should get 405 Method Not Allowed (ReadOnlyModelViewSet)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cannot_update_transaction_via_api(self):
        """Cannot update transactions via API (immutable)"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('pointstransaction-detail', args=[self.tx1.id])
        data = {'activator_points': 999}
        response = self.client.patch(url, data)
        
        # Should get 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cannot_delete_transaction_via_api(self):
        """Cannot delete transactions via API (immutable)"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('pointstransaction-detail', args=[self.tx1.id])
        response = self.client.delete(url)
        
        # Should get 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PointsTransactionBatchAPITest(TestCase):
    """Test Points Transaction Batch API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        
        # Create batch
        self.batch = PointsTransactionBatch.objects.create(
            name="Test Batch",
            description="Test batch for API",
            created_by=self.user
        )
        
        # Create transactions in batch
        category = BunkerCategory.objects.create(name_pl='Test', name_en='Test')
        bunker = Bunker.objects.create(
            reference_number='SP-0001',
            name_en='Test',
            name_pl='Test',
            category=category,
            latitude=Decimal('52.0'),
            longitude=Decimal('15.0')
        )
        
        log1 = ActivationLog.objects.create(
            user=self.user,
            activator=self.user,
            bunker=bunker,
            activation_date=timezone.now(),
            mode='SSB'
        )
        log2 = ActivationLog.objects.create(
            user=self.user,
            activator=self.user,
            bunker=bunker,
            activation_date=timezone.now() + timedelta(minutes=5),  # Different time
            mode='CW'
        )
        
        tx1 = PointsService.award_activator_points(
            user=self.user, activation_log=log1, created_by=self.user
        )
        tx2 = PointsService.award_activator_points(
            user=self.user, activation_log=log2, created_by=self.user
        )
        
        self.batch.transactions.add(tx1, tx2)
    
    def test_list_batches(self):
        """Can list transaction batches"""
        url = reverse('pointstransactionbatch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_retrieve_batch(self):
        """Can retrieve batch details"""
        url = reverse('pointstransactionbatch-detail', args=[self.batch.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.batch.id)
        self.assertEqual(response.data['name'], "Test Batch")
        self.assertIn('transaction_count', response.data)
        self.assertEqual(response.data['transaction_count'], 2)
        self.assertIn('total_points_awarded', response.data)
    
    def test_batch_read_only(self):
        """Batches are read-only via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('pointstransactionbatch-list')
        data = {'name': 'New Batch'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
