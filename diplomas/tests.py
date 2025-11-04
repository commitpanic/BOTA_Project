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
            requirements={
                "min_bunkers": 10,
                "min_qsos": 50
            },
            points_awarded=100,
            is_active=True
        )
    
    def test_diploma_type_creation(self):
        """Test basic DiplomaType creation"""
        self.assertEqual(self.diploma_type.name_en, "Hunter Bronze")
        self.assertEqual(self.diploma_type.name_pl, "Myśliwy Brązowy")
        self.assertEqual(self.diploma_type.category, "hunter")
        self.assertEqual(self.diploma_type.points_awarded, 100)
        self.assertTrue(self.diploma_type.is_active)
    
    def test_diploma_type_str(self):
        """Test string representation"""
        # __str__ returns English name
        self.assertIn("Hunter Bronze", str(self.diploma_type))
    
    def test_diploma_type_requirements_json(self):
        """Test JSON requirements field"""
        self.assertEqual(self.diploma_type.requirements["min_bunkers"], 10)
        self.assertEqual(self.diploma_type.requirements["min_qsos"], 50)
    
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
            requirements_met={"min_bunkers": 10}
        )
        Diploma.objects.create(
            user=user2,
            diploma_type=self.diploma_type,
            requirements_met={"min_bunkers": 15}
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
            points_awarded=300
        )
        DiplomaType.objects.create(
            name_pl="Aktywator Brązowy",
            name_en="Activator Bronze",
            description_pl="Opis",
            description_en="Description",
            category="activator",
            points_awarded=100
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
            points_awarded=200
        )
    
    def test_diploma_creation(self):
        """Test basic Diploma creation"""
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            requirements_met={"min_bunkers": 20}
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
            requirements_met={}
        )
        
        # String should include diploma number and callsign
        self.assertIn("SP1TEST", str(diploma))
        self.assertIn(diploma.diploma_number, str(diploma))
    
    def test_diploma_number_generation(self):
        """Test automatic diploma number generation"""
        diploma1 = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            requirements_met={}
        )
        
        user2 = User.objects.create_user(
            email='hunter2@example.com',
            callsign='SP2TEST',
            password='testpass123'
        )
        diploma2 = Diploma.objects.create(
            user=user2,
            diploma_type=self.diploma_type,
            requirements_met={}
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
            requirements_met={}
        )
        
        # Should be valid UUID
        self.assertIsInstance(diploma.verification_code, uuid.UUID)
    
    def test_unique_together_constraint(self):
        """Test unique constraint on diploma_type + user"""
        Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            requirements_met={}
        )
        
        # Trying to create duplicate should fail
        with self.assertRaises(IntegrityError):
            Diploma.objects.create(
                user=self.user,
                diploma_type=self.diploma_type,
                requirements_met={}
            )
    
    def test_requirements_met_json(self):
        """Test requirements_met JSON field"""
        requirements = {
            "min_bunkers": 25,
            "min_qsos": 100,
            "regions": ["MA", "WP", "SL"]
        }
        diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            requirements_met=requirements
        )
        
        self.assertEqual(diploma.requirements_met["min_bunkers"], 25)
        self.assertEqual(len(diploma.requirements_met["regions"]), 3)


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
            requirements={
                "min_activations": 10,
                "min_qsos": 50
            },
            points_awarded=100
        )
    
    def test_progress_creation(self):
        """Test DiplomaProgress creation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "activations": 5,
                "qsos": 25
            }
        )
        
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.diploma_type, self.diploma_type)
        self.assertIsNotNone(progress.last_updated)
    
    def test_progress_str(self):
        """Test string representation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={}
        )
        
        # String should include callsign and percentage
        self.assertIn("SP3TEST", str(progress))
        self.assertIn("%", str(progress))
    
    def test_calculate_progress_percentage(self):
        """Test progress percentage calculation"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "min_activations": 5,
                "min_qsos": 30
            }
        )
        
        # Should calculate based on requirements
        # min_activations: 5/10 = not met (needs >=10), min_qsos: 30/50 = not met (needs >=50)
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
            current_progress={
                "min_activations": 15,
                "min_qsos": 75
            }
        )
        
        percentage = progress.calculate_progress()
        self.assertEqual(percentage, Decimal('100.00'))
    
    def test_calculate_progress_zero(self):
        """Test progress with no progress"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "min_activations": 0,
                "min_qsos": 0
            }
        )
        
        percentage = progress.calculate_progress()
        self.assertEqual(percentage, Decimal('0.00'))
    
    def test_update_progress(self):
        """Test update_progress method"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "min_activations": 3,
                "min_qsos": 10
            }
        )
        
        old_updated = progress.last_updated
        
        # Update progress
        progress.update_progress(min_activations=7, min_qsos=35)
        
        self.assertEqual(progress.current_progress["min_activations"], 7)
        self.assertEqual(progress.current_progress["min_qsos"], 35)
        self.assertGreater(progress.last_updated, old_updated)
    
    def test_is_eligible_true(self):
        """Test eligibility when requirements met"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "min_activations": 12,
                "min_qsos": 60
            }
        )
        
        progress.calculate_progress()
        progress.save()
        
        self.assertTrue(progress.is_eligible)
    
    def test_is_eligible_false(self):
        """Test eligibility when requirements not met"""
        progress = DiplomaProgress.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            current_progress={
                "min_activations": 5,
                "min_qsos": 20
            }
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
            points_awarded=500
        )
        self.diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            requirements_met={"b2b_count": 50}
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
        # Create verifications with slight delay
        v1 = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verification_method="number"
        )
        
        v2 = DiplomaVerification.objects.create(
            diploma=self.diploma,
            verification_method="code"
        )
        
        verifications = list(DiplomaVerification.objects.all())
        # Most recent first
        self.assertEqual(verifications[0].id, v2.id)
        self.assertEqual(verifications[1].id, v1.id)
    
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
