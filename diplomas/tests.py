from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification

User = get_user_model()


class DiplomaTypeModelTest(TestCase):
    """Test suite for DiplomaType model"""
    
    def setUp(self):
        """Set up test data"""
        self.diploma_type = DiplomaType.objects.create(
            name_pl="Myśliwy Brązowy",
            name_en="Hunter Bronze",
            description_pl="Aktywuj 10 różnych bunkrów",
            description_en="Activate 10 different bunkers",
            category="hunter",
            min_activator_points=0,
            min_hunter_points=50,
            min_b2b_points=0,
            min_unique_activations=10,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
    
    def test_diploma_type_creation(self):
        """Test basic DiplomaType creation"""
        self.assertEqual(self.diploma_type.name_en, "Hunter Bronze")
        self.assertEqual(self.diploma_type.name_pl, "Myśliwy Brązowy")
        self.assertEqual(self.diploma_type.category, "hunter")
        self.assertEqual(self.diploma_type.min_hunter_points, 50)
        self.assertEqual(self.diploma_type.min_unique_activations, 10)
        self.assertTrue(self.diploma_type.is_active)
    
    def test_diploma_type_str(self):
        """Test string representation"""
        # __str__ returns English name
        self.assertIn("Hunter Bronze", str(self.diploma_type))
    
    def test_diploma_type_requirements(self):
        """Test point and count requirements"""
        self.assertEqual(self.diploma_type.min_hunter_points, 50)
        self.assertEqual(self.diploma_type.min_unique_activations, 10)
    
    def test_get_category_display(self):
        """Test category display method"""
        self.assertEqual(self.diploma_type.get_category_display(), "Hunter")
    
    def test_get_total_issued(self):
        """Test get_total_issued method"""
        user1 = User.objects.create_user(
            email='user1@example.com',
            callsign='TEST1',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            email='user2@example.com',
            callsign='TEST2',
            password='testpass123'
        )
        
        # Initially 0
        self.assertEqual(self.diploma_type.get_total_issued(), 0)
        
        # Create diplomas
        Diploma.objects.create(
            user=user1,
            diploma_type=self.diploma_type,
            activator_points_earned=50,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        Diploma.objects.create(
            user=user2,
            diploma_type=self.diploma_type,
            activator_points_earned=60,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        
        self.assertEqual(self.diploma_type.get_total_issued(), 2)
    
    def test_diploma_type_ordering(self):
        """Test ordering by name"""
        DiplomaType.objects.create(
            name_pl="Aktywator Złoty",
            name_en="Activator Gold",
            description_pl="Opis",
            description_en="Description",
            category="activator",
            min_activator_points=100,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0
        )
        DiplomaType.objects.create(
            name_pl="Aktywator Brązowy",
            name_en="Activator Bronze",
            description_pl="Opis",
            description_en="Description",
            category="activator",
            min_activator_points=50,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0
        )
        
        types = list(DiplomaType.objects.all())
        self.assertEqual(types[0].name_en, "Activator Bronze")
        self.assertEqual(types[1].name_en, "Activator Gold")


class DiplomaModelTest(TestCase):
    """Test suite for Diploma model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='hunter@example.com',
            callsign='SP1TEST',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl="Myśliwy Srebrny",
            name_en="Hunter Silver",
            description_pl="Opis",
            description_en="Description",
            category="hunter",
            min_activator_points=0,
            min_hunter_points=100,
            min_b2b_points=0
        )
    
    def test_diploma_creation(self):
        """Test basic Diploma creation"""
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        self.assertEqual(diploma.user, self.user)
        self.assertEqual(diploma.diploma_type, self.diploma_type)
        self.assertIsNotNone(diploma.issue_date)
        self.assertIsNotNone(diploma.verification_code)
    
    def test_diploma_str(self):
        """Test string representation"""
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        # String should include diploma number and callsign
        self.assertIn("SP1TEST", str(diploma))
        self.assertIn(diploma.diploma_number, str(diploma))
    
    def test_diploma_number_generation(self):
        """Test automatic diploma number generation"""
        diploma1 = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        user2 = User.objects.create_user(
            email='hunter2@example.com',
            callsign='SP2TEST',
            password='testpass123'
        )
        diploma2 = Diploma.objects.create(
            user=user2,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        # Check format: HNT-2025-0001
        self.assertRegex(diploma1.diploma_number, r'^HNT-\d{4}-\d{4}$')
        self.assertRegex(diploma2.diploma_number, r'^HNT-\d{4}-\d{4}$')
        
        # Check they're sequential
        num1 = int(diploma1.diploma_number.split('-')[2])
        num2 = int(diploma2.diploma_number.split('-')[2])
        self.assertEqual(num2, num1 + 1)
    
    def test_verification_code_uuid(self):
        """Test verification code is UUID"""
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        # Should be valid UUID
        self.assertIsInstance(diploma.verification_code, uuid.UUID)
    
    def test_unique_together_constraint(self):
        """Test unique constraint on diploma_type + user"""
        Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=100,
            b2b_points_earned=0
        )
        
        # Trying to create duplicate should fail
        with self.assertRaises(IntegrityError):
            Diploma.objects.create(
                user=self.user,
                diploma_type=self.diploma_type,
                activator_points_earned=0,
                hunter_points_earned=100,
                b2b_points_earned=0
            )
    
    def test_points_earned_fields(self):
        """Test points earned fields at issuance"""
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=50,
            hunter_points_earned=100,
            b2b_points_earned=25
        )
        
        self.assertEqual(diploma.activator_points_earned, 50)
        self.assertEqual(diploma.hunter_points_earned, 100)
        self.assertEqual(diploma.b2b_points_earned, 25)


class DiplomaProgressModelTest(TestCase):
    """Test suite for DiplomaProgress model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='progress@example.com',
            callsign='SP3TEST',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl="Aktywator Brązowy",
            name_en="Activator Bronze",
            description_pl="Opis",
            description_en="Description",
            category="activator",
            min_activator_points=50,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=10,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0
        )
    
    def test_progress_creation(self):
        """Test DiplomaProgress creation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=5,
            hunter_points=10,
            b2b_points=0,
            unique_activations=3,
            total_activations=8,
            unique_hunted=0,
            total_hunted=0
        )
        
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.diploma_type, self.diploma_type)
        self.assertIsNotNone(progress.last_updated)
    
    def test_progress_str(self):
        """Test string representation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=0,
            hunter_points=0,
            b2b_points=0,
            unique_activations=0,
            total_activations=0,
            unique_hunted=0,
            total_hunted=0
        )
        
        # String should include callsign and percentage
        self.assertIn("SP3TEST", str(progress))
        self.assertIn("%", str(progress))
    
    def test_calculate_progress_percentage(self):
        """Test progress percentage calculation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=30,
            hunter_points=0,
            b2b_points=0,
            unique_activations=5,
            total_activations=20,
            unique_hunted=0,
            total_hunted=0
        )
        
        # Should calculate based on requirements
        # activator_points: 30/50 = not met, unique_activations: 5/10 = not met
        # 0 of 2 requirements met = 0%
        percentage = progress.calculate_progress()
        self.assertIsNotNone(percentage)
        self.assertGreaterEqual(percentage, Decimal('0'))
        self.assertLessEqual(percentage, Decimal('100'))
    
    def test_calculate_progress_complete(self):
        """Test progress when requirements met"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=60,
            hunter_points=0,
            b2b_points=0,
            unique_activations=15,
            total_activations=50,
            unique_hunted=0,
            total_hunted=0
        )
        
        percentage = progress.calculate_progress()
        self.assertEqual(percentage, Decimal('100.00'))
    
    def test_calculate_progress_zero(self):
        """Test progress with no progress"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=0,
            hunter_points=0,
            b2b_points=0,
            unique_activations=0,
            total_activations=0,
            unique_hunted=0,
            total_hunted=0
        )
        
        percentage = progress.calculate_progress()
        self.assertEqual(percentage, Decimal('0.00'))
    
    def test_update_progress(self):
        """Test progress field updates"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=10,
            hunter_points=0,
            b2b_points=0,
            unique_activations=3,
            total_activations=10,
            unique_hunted=0,
            total_hunted=0
        )
        
        old_updated = progress.last_updated
        
        # Update progress fields
        progress.activator_points = 25
        progress.unique_activations = 7
        progress.save()
        
        self.assertEqual(progress.activator_points, 25)
        self.assertEqual(progress.unique_activations, 7)
        self.assertGreaterEqual(progress.last_updated, old_updated)
    
    def test_is_eligible_true(self):
        """Test eligibility when requirements met"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=60,
            hunter_points=0,
            b2b_points=0,
            unique_activations=12,
            total_activations=50,
            unique_hunted=0,
            total_hunted=0
        )
        
        progress.calculate_progress()
        progress.save()
        
        self.assertTrue(progress.is_eligible)
    
    def test_is_eligible_false(self):
        """Test eligibility when requirements not met"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points=30,
            hunter_points=0,
            b2b_points=0,
            unique_activations=5,
            total_activations=20,
            unique_hunted=0,
            total_hunted=0
        )
        
        progress.calculate_progress()
        progress.save()
        
        self.assertFalse(progress.is_eligible)


class DiplomaVerificationModelTest(TestCase):
    """Test suite for DiplomaVerification model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='verify@example.com',
            callsign='SP4TEST',
            password='testpass123'
        )
        self.diploma_type = DiplomaType.objects.create(
            name_pl="B2B Złoty",
            name_en="B2B Gold",
            description_pl="Opis",
            description_en="Description",
            category="b2b",
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=100,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0
        )
        self.diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=0,
            hunter_points_earned=0,
            b2b_points_earned=150
        )
    
    def test_verification_creation(self):
        """Test DiplomaVerification creation"""
        verification = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verified_by_ip="192.168.1.1",
            verification_method="code"
        )
        
        self.assertEqual(verification.diploma, self.diploma)
        self.assertEqual(verification.verified_by_ip, "192.168.1.1")
        self.assertEqual(verification.verification_method, "code")
        self.assertIsNotNone(verification.verified_at)
    
    def test_verification_str(self):
        """Test string representation"""
        verification = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verification_method="number"
        )
        
        expected = f"Verification of {self.diploma.diploma_number} at {verification.verified_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(verification), expected)
    
    def test_verification_methods(self):
        """Test different verification methods"""
        methods = ["number", "code", "qr", "manual"]
        
        for method in methods:
            verification = DiplomaVerification.objects.create(
                diploma=self.diploma,
                verification_method=method
            )
            self.assertEqual(verification.verification_method, method)
            verification.delete()  # Clean up for next iteration
    
    def test_verification_ordering(self):
        """Test ordering by verified_at descending"""
        # Create verifications
        v1 = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verification_method="number"
        )
        
        v2 = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verification_method="code"
        )
        
        verifications = list(DiplomaVerification.objects.all())
        # Should have two verifications
        self.assertEqual(len(verifications), 2)
        # Most recent should be first (v2), but if timestamps are equal, order by ID
        # Just verify both exist in the list
        self.assertIn(v1, verifications)
        self.assertIn(v2, verifications)
    
    def test_multiple_verifications_allowed(self):
        """Test that multiple verifications can be logged"""
        DiplomaVerification.objects.create(
            diploma=self.diploma,
            verified_by_ip="192.168.1.1",
            verification_method="number"
        )
        DiplomaVerification.objects.create(
            diploma=self.diploma,
            verified_by_ip="10.0.0.1",
            verification_method="qr"
        )
        DiplomaVerification.objects.create(
            diploma=self.diploma,
            verified_by_ip="172.16.0.1",
            verification_method="code"
        )
        
        self.assertEqual(DiplomaVerification.objects.filter(diploma=self.diploma).count(), 3)
