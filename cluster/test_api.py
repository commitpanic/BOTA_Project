"""
API tests for cluster app.
Tests cluster management, members, and alerts.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from .models import Cluster, ClusterMember, ClusterAlert
from bunkers.models import Bunker, BunkerCategory
from decimal import Decimal

User = get_user_model()


class ClusterAPITest(TestCase):
    """Test Cluster API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.cluster = Cluster.objects.create(
            name_pl='Linia Mołotowa',
            name_en='Molotov Line',
            region='Podlaskie',
            created_by=self.user
        )
    
    def test_list_clusters(self):
        """Test listing clusters"""
        response = self.client.get('/api/clusters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_cluster(self):
        """Test retrieving a cluster"""
        response = self.client.get(f'/api/clusters/{self.cluster.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name_en'], 'Molotov Line')
    
    def test_create_cluster_authenticated(self):
        """Test creating a cluster as authenticated user"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name_pl': 'Nowa Grupa',
            'name_en': 'New Group',
            'region': 'Mazowieckie',
            'is_active': True
        }
        response = self.client.post('/api/clusters/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_filter_clusters_by_region(self):
        """Test filtering clusters by region"""
        response = self.client.get('/api/clusters/?region=Podlaskie')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ClusterMemberAPITest(TestCase):
    """Test ClusterMember API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.cluster = Cluster.objects.create(
            name_pl='Grupa',
            name_en='Group',
            created_by=self.user
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
        self.member = ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker,
            added_by=self.user
        )
    
    def test_list_members(self):
        """Test listing cluster members"""
        response = self.client.get('/api/cluster-members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_members_by_cluster(self):
        """Test filtering members by cluster"""
        response = self.client.get(f'/api/cluster-members/?cluster={self.cluster.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ClusterAlertAPITest(TestCase):
    """Test ClusterAlert API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.cluster = Cluster.objects.create(
            name_pl='Grupa',
            name_en='Group',
            created_by=self.user
        )
        self.alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl='Uwaga',
            title_en='Alert',
            message_pl='Wiadomość',
            message_en='Message',
            alert_type='info',
            start_date=timezone.now(),
            created_by=self.user
        )
    
    def test_list_alerts(self):
        """Test listing alerts"""
        response = self.client.get('/api/cluster-alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_alerts_by_cluster(self):
        """Test filtering alerts by cluster"""
        response = self.client.get(f'/api/cluster-alerts/?cluster={self.cluster.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
