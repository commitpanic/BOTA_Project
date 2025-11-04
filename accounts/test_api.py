"""
API tests for accounts app.
Tests user management, authentication, statistics, and roles.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserStatistics, UserRole, UserRoleAssignment

User = get_user_model()


class UserAPITest(TestCase):
    """Test User API endpoints"""
    
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
    
    def test_list_users(self):
        """Test listing users"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_user(self):
        """Test retrieving a user"""
        response = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['callsign'], 'TEST1')
    
    def test_current_user_profile(self):
        """Test /me endpoint"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['callsign'], 'TEST1')
    
    def test_user_registration(self):
        """Test user registration"""
        data = {
            'email': 'newuser@example.com',
            'callsign': 'NEW1',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(callsign='NEW1').exists())
    
    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'email': 'newuser@example.com',
            'callsign': 'NEW1',
            'password': 'newpass123',
            'password_confirm': 'different123'
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_users_by_active(self):
        """Test filtering users by is_active"""
        self.user.is_active = False
        self.user.save()
        response = self.client.get('/api/users/?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserStatisticsAPITest(TestCase):
    """Test UserStatistics API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            callsign='USER1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            callsign='USER2',
            password='pass123'
        )
        # UserStatistics created automatically by signal
        self.stats1 = self.user1.statistics
        self.stats1.hunter_points = 100
        self.stats1.activator_points = 50
        self.stats1.save()
        
        self.stats2 = self.user2.statistics
        self.stats2.hunter_points = 200
        self.stats2.activator_points = 75
        self.stats2.save()
    
    def test_list_statistics(self):
        """Test listing statistics"""
        response = self.client.get('/api/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_leaderboard(self):
        """Test leaderboard endpoint"""
        response = self.client.get('/api/statistics/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by points (USER2 first)
        self.assertEqual(response.data[0]['user'], self.user2.id)


class UserRoleAPITest(TestCase):
    """Test UserRole and UserRoleAssignment API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            callsign='ADMIN',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            callsign='USER1',
            password='pass123'
        )
        self.role = UserRole.objects.create(
            name='Moderator',
            description='Can moderate content'
        )
    
    def test_list_roles_requires_admin(self):
        """Test that listing roles requires admin"""
        response = self.client.get('/api/roles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_roles_as_admin(self):
        """Test listing roles as admin"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_role_assignment(self):
        """Test creating role assignment"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'user': self.user.id,
            'role': self.role.id,
            'is_active': True
        }
        response = self.client.post('/api/role-assignments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserRoleAssignment.objects.filter(
                user=self.user,
                role=self.role
            ).exists()
        )
