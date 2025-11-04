"""
API tests for bunkers app.
Tests bunker management, photos, resources, and inspections.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import BunkerCategory, Bunker, BunkerPhoto, BunkerResource, BunkerInspection
from decimal import Decimal

User = get_user_model()


class BunkerCategoryAPITest(TestCase):
    """Test BunkerCategory API endpoints"""
    
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
            name_en='Shelter',
            description_pl='Opis',
            description_en='Description'
        )
    
    def test_list_categories(self):
        """Test listing categories"""
        response = self.client.get('/api/bunker-categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_category(self):
        """Test retrieving a category"""
        response = self.client.get(f'/api/bunker-categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name_en'], 'Shelter')


class BunkerAPITest(TestCase):
    """Test Bunker API endpoints"""
    
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
            name_pl='Schron Testowy',
            name_en='Test Bunker',
            category=self.category,
            latitude=Decimal('52.229676'),
            longitude=Decimal('21.012229'),
            created_by=self.user
        )
    
    def test_list_bunkers(self):
        """Test listing bunkers"""
        response = self.client.get('/api/bunkers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_bunker(self):
        """Test retrieving a bunker"""
        response = self.client.get(f'/api/bunkers/{self.bunker.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reference_number'], 'BNK-001')
    
    def test_create_bunker_authenticated(self):
        """Test creating a bunker as authenticated user"""
        self.client.force_authenticate(user=self.user)
        data = {
            'reference_number': 'BNK-002',
            'name_pl': 'Nowy Schron',
            'name_en': 'New Bunker',
            'category': self.category.id,
            'latitude': '52.5',
            'longitude': '21.0'
        }
        response = self.client.post('/api/bunkers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Bunker.objects.filter(reference_number='BNK-002').exists())
    
    def test_filter_bunkers_by_category(self):
        """Test filtering bunkers by category"""
        response = self.client.get(f'/api/bunkers/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_bunkers(self):
        """Test searching bunkers"""
        response = self.client.get('/api/bunkers/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class BunkerPhotoAPITest(TestCase):
    """Test BunkerPhoto API endpoints"""
    
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
    
    def test_list_photos(self):
        """Test listing photos"""
        response = self.client.get('/api/bunker-photos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BunkerInspectionAPITest(TestCase):
    """Test BunkerInspection API endpoints"""
    
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
    
    def test_list_inspections(self):
        """Test listing inspections"""
        response = self.client.get('/api/bunker-inspections/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_inspections_by_bunker(self):
        """Test filtering inspections by bunker"""
        response = self.client.get(f'/api/bunker-inspections/?bunker={self.bunker.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
