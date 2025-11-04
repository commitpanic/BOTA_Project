"""
API tests for diplomas app.
Tests diploma types, diplomas, progress, and verifications.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification
from bunkers.models import Bunker, BunkerCategory
from decimal import Decimal

User = get_user_model()


class DiplomaTypeAPITest(TestCase):
    """Test DiplomaType API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl='BOTA 100',
            name_en='BOTA 100',
            description_pl='Opis',
            description_en='Description',
            category='hunter',
            points_awarded=100
        )
    
    def test_list_diploma_types(self):
        """Test listing diploma types"""
        response = self.client.get('/api/diploma-types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_diploma_type(self):
        """Test retrieving a diploma type"""
        response = self.client.get(f'/api/diploma-types/{self.diploma_type.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name_en'], 'BOTA 100')


class DiplomaAPITest(TestCase):
    """Test Diploma API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl='BOTA 100',
            name_en='BOTA 100',
            description_pl='Opis',
            description_en='Description',
            category='hunter',
            points_awarded=100
        )
        self.diploma = Diploma.objects.create(
            diploma_type=self.diploma_type,
            user=self.user,
            issue_date=timezone.now(),
            diploma_number='D-001'
        )
    
    def test_list_diplomas(self):
        """Test listing diplomas"""
        response = self.client.get('/api/diplomas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_diploma(self):
        """Test retrieving a diploma"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/diplomas/{self.diploma.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['diploma_number'], 'D-001')
    
    def test_verify_diploma(self):
        """Test verifying a diploma"""
        data = {
            'diploma_number': 'D-001'
        }
        response = self.client.post('/api/diplomas/verify/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verification log should be created
        self.assertTrue(DiplomaVerification.objects.filter(diploma=self.diploma).exists())


class DiplomaProgressAPITest(TestCase):
    """Test DiplomaProgress API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl='BOTA 100',
            name_en='BOTA 100',
            description_pl='Opis',
            description_en='Description',
            category='hunter',
            points_awarded=100
        )
        self.progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={'bunkers_activated': 5},
            percentage_complete=50
        )
    
    def test_list_progress(self):
        """Test listing diploma progress"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/diploma-progress/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_progress(self):
        """Test retrieving diploma progress"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/diploma-progress/{self.progress.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['percentage_complete']), 50.0)
    
    def test_update_progress(self):
        """Test updating diploma progress"""
        self.client.force_authenticate(user=self.user)
        data = {'progress_updates': {'bunkers_activated': 10}}
        response = self.client.post(f'/api/diploma-progress/{self.progress.id}/update_progress/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DiplomaVerificationAPITest(TestCase):
    """Test DiplomaVerification API endpoints"""
    
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
        self.diploma_type = DiplomaType.objects.create(
            name_pl='BOTA 100',
            name_en='BOTA 100',
            description_pl='Opis',
            description_en='Description',
            category='hunter',
            points_awarded=100
        )
        self.diploma = Diploma.objects.create(
            diploma_type=self.diploma_type,
            user=self.user,
            issue_date=timezone.now(),
            diploma_number='D-001'
        )
        self.verification = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verified_by_ip='127.0.0.1',
            verification_method='number'
        )
    
    def test_list_verifications_admin_only(self):
        """Test listing verifications requires admin"""
        # Not authenticated
        response = self.client.get('/api/diploma-verifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Regular user
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/diploma-verifications/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/diploma-verifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
