"""
API tests for activations app.
Tests activation keys, logs, and licenses.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from .models import ActivationKey, ActivationLog, License
from bunkers.models import Bunker, BunkerCategory
from decimal import Decimal

User = get_user_model()


class ActivationKeyAPITest(TestCase):
    """Test ActivationKey API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.category = BunkerCategory.objects.create(
            name_pl='Schron',
            name_en='Shelter'
        )
        self.bunker = Bunker.objects.create(
            reference_number='BNK-001',
            name_pl='Schron',
            name_en='Bunker',
            category=self.category,
            latitude=Decimal('52.0'),
            longitude=Decimal('21.0')
        )
        self.key = ActivationKey.objects.create(
            key='TEST-KEY-1234',
            bunker=self.bunker,
            valid_from=timezone.now(),
            created_by=self.user
        )
    
    def test_list_keys(self):
        """Test listing activation keys"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/activation-keys/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_key(self):
        """Test retrieving an activation key"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/activation-keys/{self.key.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_use_key(self):
        """Test using an activation key"""
        self.client.force_authenticate(user=self.user)
        data = {
            'key': 'TEST-KEY-1234',
            'is_b2b': False
        }
        response = self.client.post('/api/activation-keys/use_key/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify key was used
        self.key.refresh_from_db()
        self.assertEqual(self.key.times_used, 1)


class ActivationLogAPITest(TestCase):
    """Test ActivationLog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.category = BunkerCategory.objects.create(
            name_pl='Schron',
            name_en='Shelter'
        )
        self.bunker = Bunker.objects.create(
            reference_number='BNK-001',
            name_pl='Schron',
            name_en='Bunker',
            category=self.category,
            latitude=Decimal('52.0'),
            longitude=Decimal('21.0')
        )
        self.log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=timezone.now()
        )
    
    def test_list_logs(self):
        """Test listing activation logs"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/activation-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_logs_by_user(self):
        """Test filtering logs by user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/activation-logs/?user={self.user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LicenseAPITest(TestCase):
    """Test License API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            callsign='ADMIN',
            password='adminpass123',
            is_staff=True
        )
        self.license = License.objects.create(
            license_number='LIC-001',
            license_type='contest',
            title_pl='Licencja',
            title_en='License',
            issued_to=self.user,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            issued_by=self.admin
        )
    
    def test_list_licenses(self):
        """Test listing licenses"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/licenses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_license(self):
        """Test retrieving a license"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/licenses/{self.license.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['license_number'], 'LIC-001')
