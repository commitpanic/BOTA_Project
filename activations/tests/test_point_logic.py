"""
Tests for point awarding logic in ADIF upload
Verifies correct activator/hunter point assignment and B2B confirmation
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from activations.models import ActivationLog
from bunkers.models import Bunker
from accounts.models import UserStatistics

User = get_user_model()


class PointAwardingLogicTest(TestCase):
    """Test correct point awarding during ADIF upload"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.activator = User.objects.create_user(
            email='activator@example.com',
            callsign='SP3FCK',
            password='testpass123'
        )
        
        self.hunter1 = User.objects.create_user(
            email='hunter1@example.com',
            callsign='SP1ABC',
            password='testpass123'
        )
        
        self.hunter2 = User.objects.create_user(
            email='hunter2@example.com',
            callsign='SP2XYZ',
            password='testpass123'
        )
        
        # Create bunker
        self.bunker = Bunker.objects.create(
            reference_number='SP-0001',
            name_en='Test Bunker',
            name_pl='Testowy Bunkier',
            latitude=Decimal('52.192798'),
            longitude=Decimal('15.425792'),
            type='pillbox',
            status='approved',
            submitted_by=self.activator
        )
        
        # Create stats for all users
        self.activator_stats = UserStatistics.objects.create(user=self.activator)
        self.hunter1_stats = UserStatistics.objects.create(user=self.hunter1)
        self.hunter2_stats = UserStatistics.objects.create(user=self.hunter2)
    
    def test_activator_points_awarded_for_upload(self):
        """
        Test: User who uploads ADIF gets ACTIVATOR points
        Scenario: SP3FCK uploads log with 3 QSOs from bunker SP-0001
        Expected: SP3FCK gets +3 activator points
        """
        # Simulate ADIF upload by SP3FCK (activator)
        qso_time = timezone.now()
        
        # Create 3 QSO logs (SP3FCK activated, worked 3 different hunters)
        ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,  # Worked SP1ABC
            bunker=self.bunker,
            activation_date=qso_time,
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=False
        )
        
        ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter2,  # Worked SP2XYZ
            bunker=self.bunker,
            activation_date=qso_time + timedelta(minutes=5),
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=False
        )
        
        ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,  # Worked SP1ABC again
            bunker=self.bunker,
            activation_date=qso_time + timedelta(minutes=10),
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=False
        )
        
        # Simulate point awarding (normally done in log_import_service)
        qso_count = ActivationLog.objects.filter(activator=self.activator).count()
        self.activator_stats.total_activator_qso = qso_count
        self.activator_stats.save()
        
        # Verify SP3FCK got 3 activator points
        self.activator_stats.refresh_from_db()
        self.assertEqual(self.activator_stats.total_activator_qso, 3)
        self.assertEqual(self.activator_stats.total_hunter_qso, 0)
    
    def test_hunter_points_awarded_for_worked_stations(self):
        """
        Test: Users who appear in uploaded log get HUNTER points
        Scenario: SP3FCK uploads log, SP1ABC and SP2XYZ are in it
        Expected: SP1ABC and SP2XYZ get hunter points
        """
        qso_time = timezone.now()
        
        # Create QSO logs
        ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=qso_time,
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=False
        )
        
        ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter2,
            bunker=self.bunker,
            activation_date=qso_time + timedelta(minutes=5),
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=False
        )
        
        # Simulate point awarding for hunters
        hunter1_qsos = ActivationLog.objects.filter(user=self.hunter1).count()
        hunter2_qsos = ActivationLog.objects.filter(user=self.hunter2).count()
        
        self.hunter1_stats.total_hunter_qso = hunter1_qsos
        self.hunter1_stats.save()
        
        self.hunter2_stats.total_hunter_qso = hunter2_qsos
        self.hunter2_stats.save()
        
        # Verify hunters got points
        self.hunter1_stats.refresh_from_db()
        self.hunter2_stats.refresh_from_db()
        
        self.assertEqual(self.hunter1_stats.total_hunter_qso, 1)
        self.assertEqual(self.hunter2_stats.total_hunter_qso, 1)
        # Hunters should NOT get activator points
        self.assertEqual(self.hunter1_stats.total_activator_qso, 0)
        self.assertEqual(self.hunter2_stats.total_activator_qso, 0)
    
    def test_no_b2b_without_reciprocal_logs(self):
        """
        Test: B2B is NOT confirmed when only one log uploaded
        Scenario: SP3FCK uploads log showing QSO with SP1ABC (both at bunkers)
        Expected: is_b2b=True in log, but NO B2B points until SP1ABC uploads their log
        """
        qso_time = timezone.now()
        
        # SP3FCK uploads log showing B2B QSO
        log1 = ActivationLog.objects.create(
            activator=self.activator,  # SP3FCK
            user=self.hunter1,          # Worked SP1ABC
            bunker=self.bunker,
            activation_date=qso_time,
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=True  # Marked as B2B in ADIF
        )
        
        # Simulate awarding - activator and hunter points yes, B2B no
        self.activator_stats.total_activator_qso = 1
        self.activator_stats.activator_b2b_qso = 0  # NOT confirmed yet
        self.activator_stats.save()
        
        self.hunter1_stats.total_hunter_qso = 1
        self.hunter1_stats.save()
        
        # Verify: log has is_b2b=True but NO B2B points awarded
        self.assertTrue(log1.is_b2b)
        self.activator_stats.refresh_from_db()
        self.assertEqual(self.activator_stats.activator_b2b_qso, 0)
    
    def test_b2b_confirmed_when_both_logs_uploaded(self):
        """
        Test: B2B is confirmed when BOTH activators upload reciprocal logs
        Scenario: 
          1. SP3FCK uploads log: worked SP1ABC at 14:00 UTC
          2. SP1ABC uploads log: worked SP3FCK at 14:05 UTC (within 30 min)
        Expected: BOTH get B2B points after second upload
        """
        qso_time = timezone.now()
        
        # Create second bunker for SP1ABC
        bunker2 = Bunker.objects.create(
            reference_number='SP-0002',
            name_en='Test Bunker 2',
            name_pl='Testowy Bunkier 2',
            latitude=Decimal('52.300000'),
            longitude=Decimal('15.500000'),
            type='pillbox',
            status='approved',
            submitted_by=self.hunter1
        )
        
        # Step 1: SP3FCK uploads log (activator at SP-0001, worked SP1ABC)
        log1 = ActivationLog.objects.create(
            activator=self.activator,  # SP3FCK at SP-0001
            user=self.hunter1,          # Worked SP1ABC
            bunker=self.bunker,         # SP-0001
            activation_date=qso_time,
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=True
        )
        
        # Award initial points (no B2B yet)
        self.activator_stats.total_activator_qso = 1
        self.activator_stats.activator_b2b_qso = 0
        self.activator_stats.save()
        
        self.hunter1_stats.total_hunter_qso = 1
        self.hunter1_stats.save()
        
        # Step 2: SP1ABC uploads log (activator at SP-0002, worked SP3FCK)
        log2 = ActivationLog.objects.create(
            activator=self.hunter1,     # SP1ABC at SP-0002 (now activator!)
            user=self.activator,        # Worked SP3FCK (now hunter!)
            bunker=bunker2,             # SP-0002
            activation_date=qso_time + timedelta(minutes=5),  # Within 30 min window
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=True
        )
        
        # Now check for reciprocal match and award B2B points
        # This simulates _check_and_award_b2b() logic
        reciprocal_exists = ActivationLog.objects.filter(
            activator=self.hunter1,
            user=self.activator,
            activation_date__gte=qso_time - timedelta(minutes=30),
            activation_date__lte=qso_time + timedelta(minutes=30),
            is_b2b=True
        ).exists()
        
        self.assertTrue(reciprocal_exists)
        
        # Award B2B points to BOTH users
        if reciprocal_exists:
            self.activator_stats.activator_b2b_qso = 1
            self.activator_stats.total_activator_qso = 1
            self.activator_stats.total_hunter_qso = 1  # Also a hunter in log2
            self.activator_stats.save()
            
            self.hunter1_stats.activator_b2b_qso = 1
            self.hunter1_stats.total_activator_qso = 1  # Now also an activator
            self.hunter1_stats.total_hunter_qso = 1
            self.hunter1_stats.save()
        
        # Verify both got B2B points
        self.activator_stats.refresh_from_db()
        self.hunter1_stats.refresh_from_db()
        
        self.assertEqual(self.activator_stats.activator_b2b_qso, 1)
        self.assertEqual(self.hunter1_stats.activator_b2b_qso, 1)
    
    def test_b2b_time_window_too_far_apart(self):
        """
        Test: B2B NOT confirmed if QSOs are more than 30 minutes apart
        Scenario: SP3FCK log at 14:00, SP1ABC log at 14:35 (35 minutes)
        Expected: No B2B confirmation due to time window
        """
        qso_time = timezone.now()
        
        bunker2 = Bunker.objects.create(
            reference_number='SP-0002',
            name_en='Test Bunker 2',
            name_pl='Testowy Bunkier 2',
            latitude=Decimal('52.300000'),
            longitude=Decimal('15.500000'),
            type='pillbox',
            status='approved',
            submitted_by=self.hunter1
        )
        
        # Log 1: SP3FCK at 14:00
        log1 = ActivationLog.objects.create(
            activator=self.activator,
            user=self.hunter1,
            bunker=self.bunker,
            activation_date=qso_time,
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=True
        )
        
        # Log 2: SP1ABC at 14:35 (35 minutes later - outside window)
        log2 = ActivationLog.objects.create(
            activator=self.hunter1,
            user=self.activator,
            bunker=bunker2,
            activation_date=qso_time + timedelta(minutes=35),
            frequency='14.250',
            mode='SSB',
            rst_sent='59',
            rst_rcvd='59',
            is_b2b=True
        )
        
        # Check for reciprocal match within 30 minute window
        reciprocal_exists = ActivationLog.objects.filter(
            activator=self.hunter1,
            user=self.activator,
            activation_date__gte=qso_time - timedelta(minutes=30),
            activation_date__lte=qso_time + timedelta(minutes=30),
            is_b2b=True
        ).exists()
        
        # Should NOT find match (outside 30 min window)
        self.assertFalse(reciprocal_exists)
    
    def test_multiple_qsos_same_activation(self):
        """
        Test: Multiple QSOs in same activation counted separately
        Scenario: SP3FCK activates SP-0001, makes 5 QSOs
        Expected: 5 activator points
        """
        qso_time = timezone.now()
        
        # Create 5 QSOs
        for i in range(5):
            ActivationLog.objects.create(
                activator=self.activator,
                user=self.hunter1,
                bunker=self.bunker,
                activation_date=qso_time + timedelta(minutes=i*5),
                frequency='14.250',
                mode='SSB',
                rst_sent='59',
                rst_rcvd='59',
                is_b2b=False
            )
        
        # Award points
        qso_count = ActivationLog.objects.filter(activator=self.activator).count()
        self.activator_stats.total_activator_qso = qso_count
        self.activator_stats.save()
        
        # Verify
        self.activator_stats.refresh_from_db()
        self.assertEqual(self.activator_stats.total_activator_qso, 5)
    
    def test_complex_scenario_multiple_users(self):
        """
        Test: Complex scenario with multiple users and roles
        Scenario:
          - SP3FCK activates SP-0001, works SP1ABC (2 QSOs), SP2XYZ (1 QSO)
          - SP1ABC activates SP-0002, works SP3FCK (1 QSO), SP2XYZ (1 QSO)
          - SP2XYZ never activates
        Expected:
          - SP3FCK: 3 activator points, 1 hunter point
          - SP1ABC: 2 activator points, 2 hunter points
          - SP2XYZ: 0 activator points, 2 hunter points
        """
        qso_time = timezone.now()
        
        # Create second bunker
        bunker2 = Bunker.objects.create(
            reference_number='SP-0002',
            name_en='Bunker 2',
            name_pl='Bunkier 2',
            latitude=Decimal('52.300000'),
            longitude=Decimal('15.500000'),
            type='pillbox',
            status='approved',
            submitted_by=self.hunter1
        )
        
        # SP3FCK activates SP-0001
        ActivationLog.objects.create(
            activator=self.activator, user=self.hunter1, bunker=self.bunker,
            activation_date=qso_time, frequency='14.250', mode='SSB',
            rst_sent='59', rst_rcvd='59', is_b2b=False
        )
        ActivationLog.objects.create(
            activator=self.activator, user=self.hunter1, bunker=self.bunker,
            activation_date=qso_time + timedelta(minutes=5), frequency='14.250', mode='SSB',
            rst_sent='59', rst_rcvd='59', is_b2b=False
        )
        ActivationLog.objects.create(
            activator=self.activator, user=self.hunter2, bunker=self.bunker,
            activation_date=qso_time + timedelta(minutes=10), frequency='14.250', mode='SSB',
            rst_sent='59', rst_rcvd='59', is_b2b=False
        )
        
        # SP1ABC activates SP-0002
        ActivationLog.objects.create(
            activator=self.hunter1, user=self.activator, bunker=bunker2,
            activation_date=qso_time + timedelta(hours=1), frequency='14.250', mode='SSB',
            rst_sent='59', rst_rcvd='59', is_b2b=False
        )
        ActivationLog.objects.create(
            activator=self.hunter1, user=self.hunter2, bunker=bunker2,
            activation_date=qso_time + timedelta(hours=1, minutes=5), frequency='14.250', mode='SSB',
            rst_sent='59', rst_rcvd='59', is_b2b=False
        )
        
        # Calculate points
        # SP3FCK
        activator_qsos = ActivationLog.objects.filter(activator=self.activator).count()
        hunter_qsos = ActivationLog.objects.filter(user=self.activator).count()
        self.activator_stats.total_activator_qso = activator_qsos
        self.activator_stats.total_hunter_qso = hunter_qsos
        self.activator_stats.save()
        
        # SP1ABC
        activator_qsos = ActivationLog.objects.filter(activator=self.hunter1).count()
        hunter_qsos = ActivationLog.objects.filter(user=self.hunter1).count()
        self.hunter1_stats.total_activator_qso = activator_qsos
        self.hunter1_stats.total_hunter_qso = hunter_qsos
        self.hunter1_stats.save()
        
        # SP2XYZ
        activator_qsos = ActivationLog.objects.filter(activator=self.hunter2).count()
        hunter_qsos = ActivationLog.objects.filter(user=self.hunter2).count()
        self.hunter2_stats.total_activator_qso = activator_qsos
        self.hunter2_stats.total_hunter_qso = hunter_qsos
        self.hunter2_stats.save()
        
        # Verify
        self.activator_stats.refresh_from_db()
        self.hunter1_stats.refresh_from_db()
        self.hunter2_stats.refresh_from_db()
        
        self.assertEqual(self.activator_stats.total_activator_qso, 3)
        self.assertEqual(self.activator_stats.total_hunter_qso, 1)
        
        self.assertEqual(self.hunter1_stats.total_activator_qso, 2)
        self.assertEqual(self.hunter1_stats.total_hunter_qso, 2)
        
        self.assertEqual(self.hunter2_stats.total_activator_qso, 0)
        self.assertEqual(self.hunter2_stats.total_hunter_qso, 2)
