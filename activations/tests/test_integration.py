"""
Integration tests for ADIF upload workflow and diploma system.
Tests the complete end-to-end flow from ADIF upload to diploma awarding.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime

from bunkers.models import Bunker, BunkerCategory
from activations.models import ActivationLog
from activations.log_import_service import LogImportService
from diplomas.models import DiplomaType, Diploma, DiplomaProgress
from accounts.models import UserStatistics

User = get_user_model()


class ADIFUploadIntegrationTest(TransactionTestCase):
    """
    Integration tests for ADIF upload workflow.
    Uses TransactionTestCase to test database transactions properly.
    """
    
    def setUp(self):
        """Set up test data"""
        # Create bunker category
        self.category = BunkerCategory.objects.create(
            name_en="WW2 Bunker",
            name_pl="Bunkier z II WŚ",
            description_en="World War 2 fortification",
            description_pl="Fortyfikacja z czasów II WŚ"
        )
        
        # Create test bunkers
        self.bunker1 = Bunker.objects.create(
            reference_number="B/SP-0039",
            name_en="Test Bunker 1",
            name_pl="Testowy Bunkier 1",
            description_en="Test bunker",
            description_pl="Testowy bunkier",
            category=self.category,
            latitude=Decimal('50.123456'),
            longitude=Decimal('19.123456'),
            is_verified=True
        )
        
        self.bunker2 = Bunker.objects.create(
            reference_number="B/SP-0040",
            name_en="Test Bunker 2",
            name_pl="Testowy Bunkier 2",
            description_en="Test bunker 2",
            description_pl="Testowy bunkier 2",
            category=self.category,
            latitude=Decimal('50.223456'),
            longitude=Decimal('19.223456'),
            is_verified=True
        )
        
        # Create activator user
        self.activator = User.objects.create_user(
            email='activator@example.com',
            callsign='SP3FCK',
            password='testpass123'
        )
        
        # Create diploma types for testing
        self.diploma_activator_bronze = DiplomaType.objects.create(
            name_pl="Aktywator Brązowy",
            name_en="Activator Bronze",
            description_pl="50 punktów aktywatora",
            description_en="50 activator points",
            category="activator",
            min_activator_points=50,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
        self.diploma_explorer = DiplomaType.objects.create(
            name_pl="Eksplorator",
            name_en="Explorer",
            description_pl="10 unikalnych aktywacji",
            description_en="10 unique activations",
            category="activator",
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=10,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
        self.diploma_hunter_bronze = DiplomaType.objects.create(
            name_pl="Łowca Brązowy",
            name_en="Hunter Bronze",
            description_pl="50 punktów łowcy",
            description_en="50 hunter points",
            category="hunter",
            min_activator_points=0,
            min_hunter_points=50,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
        self.diploma_b2b_bronze = DiplomaType.objects.create(
            name_pl="B2B Brązowy",
            name_en="B2B Bronze",
            description_pl="25 punktów B2B",
            description_en="25 B2B points",
            category="b2b",
            min_activator_points=0,
            min_hunter_points=0,
            min_b2b_points=25,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
    def test_basic_adif_upload_and_points(self):
        """Test basic ADIF upload awards points correctly"""
        # Sample ADIF with 2 QSOs
        adif_content = """
<ADIF_VER:5>3.1.0
<PROGRAMID:4>TEST
<OPERATOR:6>SP3FCK
<EOH>

<CALL:6>SP3BLZ<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<RST_SENT:2>59<RST_RCVD:2>59<EOR>
<CALL:6>SP4XYZ<QSO_DATE:8>20250101<TIME_ON:4>1215<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<RST_SENT:2>59<RST_RCVD:2>59<EOR>
"""
        
        # Process upload (uploader_user is the person uploading - should be activator)
        service = LogImportService()
        result = service.process_adif_upload(adif_content, self.activator)
        
        # Debug output if failed
        if not result['success']:
            print(f"\nUpload failed: {result.get('errors', result.get('error', 'Unknown error'))}")
            if result.get('warnings'):
                print(f"Warnings: {result['warnings']}")
        
        # Verify upload success
        self.assertTrue(result['success'], f"Upload failed: {result.get('errors', result.get('error', 'Unknown'))}")
        self.assertEqual(result['qsos_processed'], 2)
        self.assertEqual(result['hunters_updated'], 2)
        
        # Verify activator points
        self.activator.refresh_from_db()
        stats = self.activator.statistics
        self.assertEqual(stats.activator_points, 2)  # 1 point per QSO
        self.assertEqual(stats.total_activator_qso, 2)
        
        # Verify hunter users were created and got points
        hunter1 = User.objects.get(callsign='SP3BLZ')
        self.assertIsNotNone(hunter1)
        self.assertEqual(hunter1.statistics.hunter_points, 1)
        self.assertEqual(hunter1.statistics.total_hunter_qso, 1)
        
        hunter2 = User.objects.get(callsign='SP4XYZ')
        self.assertIsNotNone(hunter2)
        self.assertEqual(hunter2.statistics.hunter_points, 1)
        self.assertEqual(hunter2.statistics.total_hunter_qso, 1)
        
    def test_diploma_progress_auto_update(self):
        """Test that diploma progress is automatically updated after log upload"""
        # Upload ADIF with 3 QSOs
        adif_content = """
<ADIF_VER:5>3.1.0
<OPERATOR:6>SP3FCK
<EOH>
<CALL:6>SP1AAA<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP2BBB<QSO_DATE:8>20250101<TIME_ON:4>1210<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP3CCC<QSO_DATE:8>20250101<TIME_ON:4>1220<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_content, self.activator)
        
        # Check diploma progress was created
        progress = DiplomaProgress.objects.filter(
            user=self.activator,
            diploma_type=self.diploma_activator_bronze
        ).first()
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.activator_points, 3)
        self.assertEqual(progress.unique_activations, 1)  # Only 1 unique bunker
        
        # Check percentage calculation
        progress.calculate_progress()
        # 3 points / 50 required = 6%
        self.assertEqual(progress.percentage_complete, Decimal('0.00'))  # Not met yet (needs >= 50)
        self.assertFalse(progress.is_eligible)
        
    def test_diploma_auto_award_when_eligible(self):
        """Test that diploma is automatically awarded when requirements are met"""
        # Create diploma progress that's almost complete
        progress = DiplomaProgress.objects.create(
            user=self.activator,
            diploma_type=self.diploma_activator_bronze,
            activator_points=48,  # 2 points away from 50
            hunter_points=0,
            b2b_points=0,
            unique_activations=5,
            total_activations=48,
            unique_hunted=0,
            total_hunted=0
        )
        
        # Verify not eligible yet
        self.assertEqual(Diploma.objects.filter(user=self.activator).count(), 0)
        
        # Upload ADIF with 2 QSOs to reach 50 points
        adif_content = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP1TEST<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP2TEST<QSO_DATE:8>20250101<TIME_ON:4>1210<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_content, self.activator)
        
        # Check diploma was automatically awarded
        diploma = Diploma.objects.filter(
            user=self.activator,
            diploma_type=self.diploma_activator_bronze
        ).first()
        
        self.assertIsNotNone(diploma)
        self.assertEqual(diploma.activator_points_earned, 50)
        self.assertIsNotNone(diploma.diploma_number)
        self.assertIsNotNone(diploma.verification_code)
        
    def test_unique_bunker_counting(self):
        """Test that unique bunker activations are counted correctly"""
        # Upload logs for bunker 1 (multiple QSOs)
        adif_bunker1 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP1AAA<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP2BBB<QSO_DATE:8>20250101<TIME_ON:4>1210<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP3CCC<QSO_DATE:8>20250101<TIME_ON:4>1220<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_bunker1, self.activator)
        
        # Check unique activations count
        stats = self.activator.statistics
        stats.refresh_from_db()
        self.assertEqual(stats.unique_activations, 1)
        self.assertEqual(stats.total_activator_qso, 3)
        
        # Upload logs for bunker 2
        adif_bunker2 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP4DDD<QSO_DATE:8>20250102<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<EOR>
<CALL:6>SP5EEE<QSO_DATE:8>20250102<TIME_ON:4>1210<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<EOR>
"""
        
        service.process_adif_upload(adif_bunker2, self.activator)
        
        # Check unique activations increased
        stats.refresh_from_db()
        self.assertEqual(stats.unique_activations, 2)
        self.assertEqual(stats.total_activator_qso, 5)
        
    def test_b2b_detection_and_confirmation(self):
        """Test B2B QSO detection and confirmation workflow"""
        # Create second activator
        activator2 = User.objects.create_user(
            email='activator2@example.com',
            callsign='SP4ABC',
            password='testpass123'
        )
        
        # Activator 1 uploads log showing they worked Activator 2 (both at bunkers)
        adif_activator1 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP4ABC<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<SIG:4>BOTA<SIG_INFO:9>B/SP-0040<EOR>
"""
        
        service = LogImportService()
        result1 = service.process_adif_upload(adif_activator1, self.activator)
        
        # B2B should be detected but NOT confirmed yet (only one side uploaded)
        self.assertTrue(result1['success'])
        
        # Check no B2B points awarded yet
        stats1 = self.activator.statistics
        self.assertEqual(stats1.b2b_points, 0)  # Not confirmed yet
        
        # Activator 2 uploads reciprocal log within time window
        adif_activator2 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP3FCK<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<SIG:4>BOTA<SIG_INFO:9>B/SP-0039<EOR>
"""
        
        result2 = service.process_adif_upload(adif_activator2, activator2)
        self.assertTrue(result2['success'])
        
        # Now both should have B2B points (5 points each for confirmed B2B)
        stats1.refresh_from_db()
        stats2 = activator2.statistics
        
        self.assertEqual(stats1.b2b_points, 5)
        self.assertEqual(stats1.total_b2b_qso, 1)
        self.assertEqual(stats2.b2b_points, 5)
        self.assertEqual(stats2.total_b2b_qso, 1)
        
    def test_multiple_diplomas_same_upload(self):
        """Test that multiple diplomas can be earned from a single upload"""
        # Create progress close to multiple diploma thresholds
        DiplomaProgress.objects.create(
            user=self.activator,
            diploma_type=self.diploma_activator_bronze,
            activator_points=45,
            hunter_points=0,
            b2b_points=0,
            unique_activations=8,  # Close to Explorer (10 unique)
            total_activations=45,
            unique_hunted=0,
            total_hunted=0
        )
        
        DiplomaProgress.objects.create(
            user=self.activator,
            diploma_type=self.diploma_explorer,
            activator_points=45,
            hunter_points=0,
            b2b_points=0,
            unique_activations=8,  # Close to 10
            total_activations=45,
            unique_hunted=0,
            total_hunted=0
        )
        
        # Upload logs that activate 2 new unique bunkers with enough QSOs
        adif_content = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP1A<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP1B<QSO_DATE:8>20250101<TIME_ON:4>1201<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP1C<QSO_DATE:8>20250101<TIME_ON:4>1202<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP2A<QSO_DATE:8>20250102<TIME_ON:4>1300<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<EOR>
<CALL:6>SP2B<QSO_DATE:8>20250102<TIME_ON:4>1301<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_content, self.activator)
        
        # Should now have earned both diplomas
        diplomas = Diploma.objects.filter(user=self.activator)
        self.assertEqual(diplomas.count(), 2)
        
        # Verify both diploma types
        diploma_types = set(d.diploma_type for d in diplomas)
        self.assertIn(self.diploma_activator_bronze, diploma_types)
        self.assertIn(self.diploma_explorer, diploma_types)
        
    def test_hunter_points_and_unique_hunted(self):
        """Test hunter point awarding and unique bunker tracking"""
        # Create a hunter user
        hunter = User.objects.create_user(
            email='hunter@example.com',
            callsign='SP5HNT',
            password='testpass123'
        )
        
        # Activator uploads log with hunter
        adif_content = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP5HNT<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_content, self.activator)
        
        # Check hunter got points
        hunter.refresh_from_db()
        stats = hunter.statistics
        self.assertEqual(stats.hunter_points, 1)
        self.assertEqual(stats.total_hunter_qso, 1)
        self.assertEqual(stats.unique_bunkers_hunted, 1)
        
        # Hunter works same bunker again (different activator)
        activator3 = User.objects.create_user(
            email='activator3@example.com',
            callsign='SP6XYZ',
            password='testpass123'
        )
        
        adif_content2 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP5HNT<QSO_DATE:8>20250102<TIME_ON:4>1400<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service.process_adif_upload(adif_content2, activator3)
        
        # Hunter points increase but unique count stays same
        stats.refresh_from_db()
        self.assertEqual(stats.hunter_points, 2)
        self.assertEqual(stats.total_hunter_qso, 2)
        self.assertEqual(stats.unique_bunkers_hunted, 1)  # Still only 1 unique
        
        # Hunter works different bunker
        adif_content3 = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP5HNT<QSO_DATE:8>20250103<TIME_ON:4>1500<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0040<EOR>
"""
        
        service.process_adif_upload(adif_content3, self.activator)
        
        # Unique count should increase
        stats.refresh_from_db()
        self.assertEqual(stats.hunter_points, 3)
        self.assertEqual(stats.total_hunter_qso, 3)
        self.assertEqual(stats.unique_bunkers_hunted, 2)  # Now 2 unique
        
    def test_diploma_progress_percentage_calculation(self):
        """Test that diploma progress percentage is calculated correctly"""
        # Upload some QSOs
        adif_content = """
<ADIF_VER:5>3.1.0
<EOH>
<CALL:6>SP1A<QSO_DATE:8>20250101<TIME_ON:4>1200<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
<CALL:6>SP1B<QSO_DATE:8>20250101<TIME_ON:4>1201<BAND:3>20M<MODE:3>SSB<MY_SIG:4>BOTA<MY_SIG_INFO:9>B/SP-0039<EOR>
"""
        
        service = LogImportService()
        service.process_adif_upload(adif_content, self.activator)
        
        # Check progress
        progress = DiplomaProgress.objects.get(
            user=self.activator,
            diploma_type=self.diploma_explorer
        )
        
        # Explorer needs 10 unique activations, we have 1
        # 1/10 met = 0% (requirement not met)
        self.assertEqual(progress.unique_activations, 1)
        self.assertEqual(progress.percentage_complete, Decimal('0.00'))
        
        # Add progress to meet requirement
        progress.unique_activations = 10
        progress.calculate_progress()
        progress.save()
        
        # Now should be 100%
        self.assertEqual(progress.percentage_complete, Decimal('100.00'))
        self.assertTrue(progress.is_eligible)


class DiplomaAwardingIntegrationTest(TestCase):
    """Integration tests for diploma awarding system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='SP1TEST',
            password='testpass123'
        )
        
        self.diploma_type = DiplomaType.objects.create(
            name_pl="Test Diploma",
            name_en="Test Diploma",
            description_pl="Test diploma",
            description_en="Test diploma",
            category="activator",
            min_activator_points=10,
            min_hunter_points=0,
            min_b2b_points=0,
            min_unique_activations=0,
            min_total_activations=0,
            min_unique_hunted=0,
            min_total_hunted=0,
            is_active=True
        )
        
    def test_diploma_number_generation(self):
        """Test that diploma numbers are generated correctly"""
        # Create multiple diplomas
        diploma1 = Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=15,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        
        # Check format: CATEGORY-YYYY-XXXX
        self.assertIsNotNone(diploma1.diploma_number)
        self.assertTrue(diploma1.diploma_number.startswith('ACT-2025-'))
        
        # Create another user and diploma
        user2 = User.objects.create_user(
            email='test2@example.com',
            callsign='SP2TEST',
            password='testpass123'
        )
        
        diploma2 = Diploma.objects.create(
            user=user2,
            diploma_type=self.diploma_type,
            activator_points_earned=20,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        
        # Should have different numbers
        self.assertNotEqual(diploma1.diploma_number, diploma2.diploma_number)
        
        # Both should follow same format
        self.assertTrue(diploma2.diploma_number.startswith('ACT-2025-'))
        
    def test_duplicate_diploma_prevention(self):
        """Test that users can't earn the same diploma twice"""
        # Create first diploma
        Diploma.objects.create(
            user=self.user,
            diploma_type=self.diploma_type,
            activator_points_earned=15,
            hunter_points_earned=0,
            b2b_points_earned=0
        )
        
        # Try to create duplicate (should fail due to unique_together constraint)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Diploma.objects.create(
                user=self.user,
                diploma_type=self.diploma_type,
                activator_points_earned=20,
                hunter_points_earned=0,
                b2b_points_earned=0
            )
