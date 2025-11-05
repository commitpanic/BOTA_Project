from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from bunkers.models import Bunker, BunkerCategory
from .models import PlannedActivation

User = get_user_model()


class PlannedActivationModelTest(TestCase):
    """Test PlannedActivation model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        
        self.category = BunkerCategory.objects.create(
            name_pl='Test Category',
            name_en='Test Category'
        )
        
        self.bunker = Bunker.objects.create(
            reference_number='TEST-001',
            name_pl='Test Bunker',
            name_en='Test Bunker',
            category=self.category,
            latitude=52.0,
            longitude=21.0,
            is_verified=True
        )
    
    def test_create_planned_activation(self):
        """Test creating a planned activation"""
        activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=7),
            planned_time_start=time(10, 0),
            planned_time_end=time(14, 0),
            callsign='SP3TEST',
            bands='20m, 40m, 80m',
            modes='CW, SSB',
            comments='Test activation'
        )
        
        self.assertEqual(activation.user, self.user)
        self.assertEqual(activation.bunker, self.bunker)
        self.assertEqual(activation.callsign, 'SP3TEST')
        self.assertEqual(activation.bands, '20m, 40m, 80m')
        self.assertEqual(activation.modes, 'CW, SSB')
    
    def test_str_representation(self):
        """Test string representation"""
        activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date(2025, 12, 31),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        
        expected = f"SP3TEST @ TEST-001 on 2025-12-31"
        self.assertEqual(str(activation), expected)
    
    def test_is_past_method(self):
        """Test is_past method"""
        # Past activation
        past_activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() - timedelta(days=7),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        self.assertTrue(past_activation.is_past())
        
        # Future activation
        future_activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=1),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        self.assertFalse(future_activation.is_past())


class PlannedActivationViewTest(TestCase):
    """Test PlannedActivation views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            callsign='SP3OTHER',
            password='testpass123'
        )
        
        self.category = BunkerCategory.objects.create(
            name_pl='Test Category',
            name_en='Test Category'
        )
        
        self.bunker = Bunker.objects.create(
            reference_number='TEST-001',
            name_pl='Test Bunker',
            name_en='Test Bunker',
            category=self.category,
            latitude=52.0,
            longitude=21.0,
            is_verified=True
        )
        
        self.activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=7),
            planned_time_start=time(10, 0),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
    
    def test_list_view_requires_login(self):
        """Test that list view requires authentication"""
        response = self.client.get(reverse('planned_activation_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_list_view_authenticated(self):
        """Test list view with authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
        self.assertContains(response, 'SP3TEST')
    
    def test_detail_view(self):
        """Test detail view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_detail', args=[self.activation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
    
    def test_create_view_post(self):
        """Test creating a new activation"""
        self.client.login(email='test@example.com', password='testpass123')
        data = {
            'bunker': self.bunker.pk,
            'planned_date': (date.today() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'planned_time_start': '12:00',
            'callsign': 'SP3TEST',
            'bands': '40m, 80m',
            'modes': 'SSB, FT8',
            'comments': 'New test activation'
        }
        response = self.client.post(reverse('planned_activation_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlannedActivation.objects.count(), 2)
    
    def test_edit_view_owner(self):
        """Test that owner can edit their activation"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_edit', args=[self.activation.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_edit_view_not_owner(self):
        """Test that non-owner cannot edit activation"""
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_edit', args=[self.activation.pk]))
        # Should redirect to detail page instead of showing form
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('planned_activation_detail', args=[self.activation.pk]))
    
    def test_delete_view_owner(self):
        """Test that owner can delete their activation"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(reverse('planned_activation_delete', args=[self.activation.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlannedActivation.objects.count(), 0)
    
    def test_delete_view_not_owner(self):
        """Test that non-owner cannot delete activation"""
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.post(reverse('planned_activation_delete', args=[self.activation.pk]))
        # Should redirect to detail page instead of deleting
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('planned_activation_detail', args=[self.activation.pk]))
        self.assertEqual(PlannedActivation.objects.count(), 1)
    
    def test_list_view_search(self):
        """Test search functionality"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_list') + '?search=TEST-001')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
    
    def test_filter_past_activations(self):
        """Test filtering past activations"""
        # Create past activation
        past_activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() - timedelta(days=7),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_list') + '?show_past=yes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(past_activation.planned_date))


class PlannedActivationPermissionTest(TestCase):
    """Test permissions for staff and superusers"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            callsign='SP3STAFF',
            password='testpass123',
            is_staff=True
        )
        
        self.super_user = User.objects.create_superuser(
            email='super@example.com',
            callsign='SP3SUPER',
            password='testpass123'
        )
        
        self.category = BunkerCategory.objects.create(
            name_pl='Test Category',
            name_en='Test Category'
        )
        
        self.bunker = Bunker.objects.create(
            reference_number='TEST-001',
            name_pl='Test Bunker',
            name_en='Test Bunker',
            category=self.category,
            latitude=52.0,
            longitude=21.0,
            is_verified=True
        )
        
        self.activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=7),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
    
    def test_staff_can_edit(self):
        """Test that staff can edit any activation"""
        self.client.login(email='staff@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_edit', args=[self.activation.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_superuser_can_edit(self):
        """Test that superuser can edit any activation"""
        self.client.login(email='super@example.com', password='testpass123')
        response = self.client.get(reverse('planned_activation_edit', args=[self.activation.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_can_delete(self):
        """Test that staff can delete any activation"""
        self.client.login(email='staff@example.com', password='testpass123')
        # Create a new activation for this test
        activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=7),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        response = self.client.post(reverse('planned_activation_delete', args=[activation.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlannedActivation.objects.filter(pk=activation.pk).exists())
    
    def test_superuser_can_delete(self):
        """Test that superuser can delete any activation"""
        # Create a new activation for this test
        activation = PlannedActivation.objects.create(
            user=self.user,
            bunker=self.bunker,
            planned_date=date.today() + timedelta(days=7),
            callsign='SP3TEST',
            bands='20m',
            modes='CW'
        )
        
        self.client.login(email='super@example.com', password='testpass123')
        response = self.client.post(reverse('planned_activation_delete', args=[activation.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlannedActivation.objects.filter(pk=activation.pk).exists())
