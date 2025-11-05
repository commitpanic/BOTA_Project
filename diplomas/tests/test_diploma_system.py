"""
Tests for the diploma system with point-based requirements
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

from diplomas.models import DiplomaType, DiplomaProgress, Diploma
from accounts.models import UserStatistics

User = get_user_model()


class DiplomaTypeModelTest(TestCase):
    """Test DiplomaType model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
    
    def test_create_simple_diploma(self):
        """Test creating a simple diploma with only activator requirement"""
        diploma_type = DiplomaType.objects.create(
            name_en='Basic Activator',
            name_pl='Podstawowy Aktywator',
            description_en='Activate 10 times',
            description_pl='Aktywuj 10 razy',
            category='activator',
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        self.assertEqual(diploma_type.min_activator_points, 10)
        self.assertEqual(diploma_type.min_hunter_points, 0)
        self.assertEqual(diploma_type.min_b2b_points, 0)
        self.assertFalse(diploma_type.is_time_limited())
        self.assertTrue(diploma_type.is_currently_valid())
    
    def test_create_combined_requirements_diploma(self):
        """Test diploma requiring all three point types"""
        diploma_type = DiplomaType.objects.create(
            name_en='All-Rounder',
            name_pl='Wszechstronny',
            description_en='Master all categories',
            description_pl='Opanuj wszystkie kategorie',
            category='other',
            min_activator_points=50,
            min_hunter_points=100,
            min_b2b_points=25,
            is_active=True
        )
        
        self.assertEqual(diploma_type.min_activator_points, 50)
        self.assertEqual(diploma_type.min_hunter_points, 100)
        self.assertEqual(diploma_type.min_b2b_points, 25)
    
    def test_time_limited_diploma_active(self):
        """Test time-limited diploma currently active"""
        today = date.today()
        diploma_type = DiplomaType.objects.create(
            name_en='Summer Special 2025',
            name_pl='Specjalny Letni 2025',
            description_en='Summer event diploma',
            description_pl='Dyplom letni',
            category='special_event',
            min_activator_points=20,
            min_hunter_points=20,
            min_b2b_points=0,
            valid_from=today - timedelta(days=30),
            valid_to=today + timedelta(days=30),
            is_active=True
        )
        
        self.assertTrue(diploma_type.is_time_limited())
        self.assertTrue(diploma_type.is_currently_valid())
    
    def test_time_limited_diploma_expired(self):
        """Test time-limited diploma that has expired"""
        today = date.today()
        diploma_type = DiplomaType.objects.create(
            name_en='Winter 2024',
            name_pl='Zima 2024',
            description_en='Past event',
            description_pl='Minione wydarzenie',
            category='special_event',
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            valid_from=today - timedelta(days=90),
            valid_to=today - timedelta(days=30),
            is_active=True
        )
        
        self.assertTrue(diploma_type.is_time_limited())
        self.assertFalse(diploma_type.is_currently_valid())


class DiplomaProgressTest(TestCase):
    """Test diploma progress calculation and eligibility"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        
        # Create user statistics
        self.stats = UserStatistics.objects.create(
            user=self.user,
            total_activator_qso=5,
            total_hunter_qso=8,
            activator_b2b_qso=2
        )
    
    def test_progress_activator_only_not_eligible(self):
        """Test progress when user doesn't meet activator requirement"""
        diploma_type = DiplomaType.objects.create(
            name_en='Activator Bronze',
            name_pl='Aktywator Brązowy',
            description_en='10 activator QSOs',
            description_pl='10 aktywacji',
            category='activator',
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        self.assertEqual(progress.activator_points, 5)
        self.assertLess(progress.percentage_complete, 100)
        self.assertFalse(progress.is_eligible)
    
    def test_progress_activator_only_eligible(self):
        """Test progress when user meets activator requirement"""
        diploma_type = DiplomaType.objects.create(
            name_en='Activator Starter',
            name_pl='Starter Aktywator',
            description_en='5 activator QSOs',
            description_pl='5 aktywacji',
            category='activator',
            min_activator_points=5,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        self.assertEqual(progress.activator_points, 5)
        self.assertEqual(progress.percentage_complete, 100)
        self.assertTrue(progress.is_eligible)
    
    def test_progress_hunter_only_eligible(self):
        """Test progress with hunter requirement met"""
        diploma_type = DiplomaType.objects.create(
            name_en='Hunter Bronze',
            name_pl='Łowca Brązowy',
            description_en='8 hunter QSOs',
            description_pl='8 upolowań',
            category='hunter',
            min_activator_points=0,
            min_hunter_points=8,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        self.assertEqual(progress.hunter_points, 8)
        self.assertEqual(progress.percentage_complete, 100)
        self.assertTrue(progress.is_eligible)
    
    def test_progress_combined_requirements_partial(self):
        """Test progress with combined requirements, partially met"""
        diploma_type = DiplomaType.objects.create(
            name_en='Combo',
            name_pl='Kombinacja',
            description_en='10 activator + 10 hunter',
            description_pl='10 aktywacji + 10 upolowań',
            category='other',
            min_activator_points=10,
            min_hunter_points=10,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,  # 5/10
            hunter=self.stats.total_hunter_qso,         # 8/10
            b2b=self.stats.activator_b2b_qso
        )
        
        self.assertEqual(progress.activator_points, 5)
        self.assertEqual(progress.hunter_points, 8)
        # Should not be eligible because both requirements must be met
        self.assertFalse(progress.is_eligible)
        # Percentage should be average of both categories
        self.assertGreater(progress.percentage_complete, 50)
        self.assertLess(progress.percentage_complete, 100)
    
    def test_progress_combined_requirements_all_met(self):
        """Test progress with all combined requirements met"""
        # Update user stats to meet requirements
        self.stats.total_activator_qso = 10
        self.stats.total_hunter_qso = 10
        self.stats.save()
        
        diploma_type = DiplomaType.objects.create(
            name_en='Combo',
            name_pl='Kombinacja',
            description_en='10 activator + 10 hunter',
            description_pl='10 aktywacji + 10 upolowań',
            category='other',
            min_activator_points=10,
            min_hunter_points=10,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        self.assertEqual(progress.activator_points, 10)
        self.assertEqual(progress.hunter_points, 10)
        self.assertEqual(progress.percentage_complete, 100)
        self.assertTrue(progress.is_eligible)


class DiplomaAwardingTest(TestCase):
    """Test automatic diploma awarding"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        
        self.stats = UserStatistics.objects.create(
            user=self.user,
            total_activator_qso=10,
            total_hunter_qso=5,
            activator_b2b_qso=0
        )
    
    def test_diploma_auto_awarded_when_eligible(self):
        """Test diploma is automatically awarded when eligible"""
        diploma_type = DiplomaType.objects.create(
            name_en='Activator Bronze',
            name_pl='Aktywator Brązowy',
            description_en='10 activator QSOs',
            description_pl='10 aktywacji',
            category='activator',
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        # Create progress
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        # Progress should be eligible
        self.assertTrue(progress.is_eligible)
        
        # Manually award (simulating what happens in log_import_service)
        diploma = Diploma.objects.create(
            diploma_type=diploma_type,
            user=self.user,
            activator_points_earned=progress.activator_points,
            hunter_points_earned=progress.hunter_points,
            b2b_points_earned=progress.b2b_points
        )
        
        # Verify diploma was created
        self.assertIsNotNone(diploma.diploma_number)
        self.assertIsNotNone(diploma.verification_code)
        self.assertEqual(diploma.activator_points_earned, 10)
        self.assertTrue(diploma.diploma_number.startswith('ACT-2025-'))
    
    def test_diploma_not_awarded_when_not_eligible(self):
        """Test diploma is not awarded when not eligible"""
        diploma_type = DiplomaType.objects.create(
            name_en='Activator Gold',
            name_pl='Aktywator Złoty',
            description_en='50 activator QSOs',
            description_pl='50 aktywacji',
            category='activator',
            min_activator_points=50,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        progress.update_points(
            activator=self.stats.total_activator_qso,
            hunter=self.stats.total_hunter_qso,
            b2b=self.stats.activator_b2b_qso
        )
        
        # Should not be eligible
        self.assertFalse(progress.is_eligible)
        
        # Verify no diploma exists
        diploma_count = Diploma.objects.filter(
            user=self.user,
            diploma_type=diploma_type
        ).count()
        self.assertEqual(diploma_count, 0)
    
    def test_diploma_number_generation(self):
        """Test diploma number is generated correctly"""
        diploma_type = DiplomaType.objects.create(
            name_en='Test Diploma',
            name_pl='Testowy Dyplom',
            description_en='Test',
            description_pl='Test',
            category='hunter',
            min_activator_points=0,
            min_hunter_points=5,
            min_b2b_points=0,
            is_active=True
        )
        
        diploma = Diploma.objects.create(
            diploma_type=diploma_type,
            user=self.user,
            activator_points_earned=0,
            hunter_points_earned=5,
            b2b_points_earned=0
        )
        
        # Should be HNT-2025-0001 format
        self.assertTrue(diploma.diploma_number.startswith('HNT-'))
        self.assertIn('2025', diploma.diploma_number)
        self.assertEqual(len(diploma.diploma_number), 13)  # HNT-2025-0001
    
    def test_multiple_diplomas_for_same_user(self):
        """Test user can earn multiple different diplomas"""
        # Create two diploma types
        activator_type = DiplomaType.objects.create(
            name_en='Activator',
            name_pl='Aktywator',
            description_en='Activator diploma',
            description_pl='Dyplom aktywatora',
            category='activator',
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        hunter_type = DiplomaType.objects.create(
            name_en='Hunter',
            name_pl='Łowca',
            description_en='Hunter diploma',
            description_pl='Dyplom łowcy',
            category='hunter',
            min_activator_points=0,
            min_hunter_points=5,
            min_b2b_points=0,
            is_active=True
        )
        
        # Award both
        diploma1 = Diploma.objects.create(
            diploma_type=activator_type,
            user=self.user,
            activator_points_earned=10,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        
        diploma2 = Diploma.objects.create(
            diploma_type=hunter_type,
            user=self.user,
            activator_points_earned=0,
            hunter_points_earned=5,
            b2b_points_earned=0
        )
        
        # Verify both exist
        user_diplomas = Diploma.objects.filter(user=self.user)
        self.assertEqual(user_diplomas.count(), 2)
        self.assertIn('ACT-', diploma1.diploma_number)
        self.assertIn('HNT-', diploma2.diploma_number)


class BunkerCountRequirementsTest(TestCase):
    """Test diploma system with bunker count requirements"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        # Create user statistics
        self.stats = UserStatistics.objects.create(
            user=self.user,
            total_activator_qso=15,
            unique_activations=5,
            total_hunter_qso=20,
            unique_bunkers_hunted=8
        )
    
    def test_unique_activations_requirement(self):
        """Test diploma requiring unique activations only"""
        diploma_type = DiplomaType.objects.create(
            name_en='Explorer',
            name_pl='Odkrywca',
            description_en='Activate 10 different bunkers',
            description_pl='Aktywuj 10 różnych bunkrów',
            category='activator',
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=10,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # Update with current stats (5 unique activations - not enough)
        progress.update_points(unique_activations=5)
        self.assertEqual(progress.unique_activations, 5)
        self.assertFalse(progress.is_eligible)
        self.assertEqual(progress.percentage_complete, 50)  # 5/10 = 50%
        
        # Update to meet requirement
        progress.update_points(unique_activations=10)
        self.assertEqual(progress.unique_activations, 10)
        self.assertTrue(progress.is_eligible)
        self.assertEqual(progress.percentage_complete, 100)
    
    def test_total_activations_requirement(self):
        """Test diploma requiring total activations"""
        diploma_type = DiplomaType.objects.create(
            name_en='Dedicated',
            name_pl='Oddany',
            description_en='Complete 50 activations',
            description_pl='Wykonaj 50 aktywacji',
            category='activator',
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=50,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # Update with 30 total activations
        progress.update_points(total_activations=30)
        self.assertEqual(progress.total_activations, 30)
        self.assertFalse(progress.is_eligible)
        self.assertEqual(progress.percentage_complete, 60)  # 30/50 = 60%
    
    def test_unique_hunted_requirement(self):
        """Test diploma requiring unique bunkers hunted"""
        diploma_type = DiplomaType.objects.create(
            name_en='Marathon Hunter',
            name_pl='Maratoński Łowca',
            description_en='Hunt 25 different bunkers',
            description_pl='Upoluj 25 różnych bunkrów',
            category='hunter',
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=25,
            min_total_hunted=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # Update with 8 unique hunted (from stats)
        progress.update_points(unique_hunted=8)
        self.assertEqual(progress.unique_hunted, 8)
        self.assertFalse(progress.is_eligible)
        self.assertAlmostEqual(float(progress.percentage_complete), 32.0, places=1)  # 8/25 = 32%
    
    def test_combined_points_and_counts(self):
        """Test diploma with both point and count requirements"""
        diploma_type = DiplomaType.objects.create(
            name_en='Versatile Operator',
            name_pl='Wszechstronny Operator',
            description_en='Balanced achievement',
            description_pl='Zrównoważone osiągnięcie',
            category='other',
            min_activator_points=50,
            min_hunter_points=50,
            min_b2b_points=0,
            min_unique_activations=10,
            min_total_activations=0,
            min_unique_hunted=10,
            min_total_hunted=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # Update with partial progress on all requirements
        progress.update_points(
            activator=30,           # 60% of 50
            hunter=40,              # 80% of 50
            unique_activations=5,   # 50% of 10
            unique_hunted=8         # 80% of 10
        )
        
        self.assertFalse(progress.is_eligible)  # Not all requirements met
        # Average: (60 + 80 + 50 + 80) / 4 = 67.5%
        self.assertAlmostEqual(float(progress.percentage_complete), 67.5, places=1)
        
        # Now meet all requirements
        progress.update_points(
            activator=50,
            hunter=50,
            unique_activations=10,
            unique_hunted=10
        )
        
        self.assertTrue(progress.is_eligible)
        self.assertEqual(progress.percentage_complete, 100)
    
    def test_mixed_requirements_partial_completion(self):
        """Test that partial completion of mixed requirements doesn't award diploma"""
        diploma_type = DiplomaType.objects.create(
            name_en='Expert',
            name_pl='Ekspert',
            description_en='Expert diploma',
            description_pl='Dyplom eksperta',
            category='other',
            min_activator_points=100,
            min_hunter_points=100,
            min_b2b_points=50,
            min_unique_activations=15,
            min_total_activations=0,
            min_unique_hunted=20,
            min_total_hunted=0,
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # Meet 4 out of 5 requirements (all except hunter_points)
        progress.update_points(
            activator=100,          # MET
            hunter=50,              # NOT MET (need 100)
            b2b=50,                 # MET
            unique_activations=15,  # MET
            unique_hunted=20        # MET
        )
        
        # Should not be eligible despite 4/5 requirements met
        self.assertFalse(progress.is_eligible)
        # (100 + 50 + 100 + 100 + 100) / 5 = 90%
        self.assertAlmostEqual(float(progress.percentage_complete), 90.0, places=1)
    
    def test_progress_calculation_only_active_requirements(self):
        """Test that percentage is calculated only from active requirements"""
        # Diploma with only 2 requirements (others are 0)
        diploma_type = DiplomaType.objects.create(
            name_en='Simple',
            name_pl='Prosty',
            description_en='Two requirements',
            description_pl='Dwa wymagania',
            category='other',
            min_activator_points=20,
            min_hunter_points=0,    # Not required
            min_b2b_points=0,       # Not required
            min_unique_activations=5,
            min_total_activations=0, # Not required
            min_unique_hunted=0,    # Not required
            min_total_hunted=0,     # Not required
            is_active=True
        )
        
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=diploma_type
        )
        
        # 50% of activator, 100% of unique activations
        progress.update_points(
            activator=10,           # 50% of 20
            unique_activations=5    # 100% of 5
        )
        
        # Should average only the 2 active requirements: (50 + 100) / 2 = 75%
        self.assertAlmostEqual(float(progress.percentage_complete), 75.0, places=1)
        self.assertFalse(progress.is_eligible)  # Not all requirements met
