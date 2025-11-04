from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import ActivationKey, ActivationLog, License
from bunkers.models import Bunker, BunkerCategory

User = get_user_model()


class ActivationKeyModelTest(TestCase):
    """Test ActivationKey model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="activator@test.com",
            callsign="ACT001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Test",
            name_en="Test"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-300",
            name_pl="Test Bunker",
            name_en="Test Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_activation_key_creation(self):
        """Test activation key is created correctly"""
        now = timezone.now()
        future = now + timedelta(days=30)
        
        key = ActivationKey.objects.create(
            key="TEST-KEY-123",
            bunker=self.bunker,
            valid_from=now,
            valid_until=future,
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(key.key, "TEST-KEY-123")
        self.assertEqual(key.bunker, self.bunker)
        self.assertTrue(key.is_active)
        self.assertEqual(key.times_used, 0)

    def test_generate_key(self):
        """Test key generation produces valid keys"""
        key1 = ActivationKey.generate_key()
        key2 = ActivationKey.generate_key()
        
        self.assertEqual(len(key1), 12)
        self.assertEqual(len(key2), 12)
        self.assertNotEqual(key1, key2)  # Should be random
        
        # Check no ambiguous characters
        self.assertNotIn('O', key1)
        self.assertNotIn('0', key1)
        self.assertNotIn('I', key1)
        self.assertNotIn('1', key1)

    def test_is_valid_now_active(self):
        """Test is_valid_now returns True for active key in date range"""
        now = timezone.now()
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)
        
        key = ActivationKey.objects.create(
            key="VALID-KEY",
            bunker=self.bunker,
            valid_from=past,
            valid_until=future,
            is_active=True
        )
        
        self.assertTrue(key.is_valid_now())

    def test_is_valid_now_inactive(self):
        """Test is_valid_now returns False for inactive key"""
        now = timezone.now()
        
        key = ActivationKey.objects.create(
            key="INACTIVE-KEY",
            bunker=self.bunker,
            valid_from=now,
            is_active=False
        )
        
        self.assertFalse(key.is_valid_now())

    def test_is_valid_now_not_started(self):
        """Test is_valid_now returns False for future key"""
        future = timezone.now() + timedelta(days=1)
        
        key = ActivationKey.objects.create(
            key="FUTURE-KEY",
            bunker=self.bunker,
            valid_from=future,
            is_active=True
        )
        
        self.assertFalse(key.is_valid_now())

    def test_is_valid_now_expired(self):
        """Test is_valid_now returns False for expired key"""
        past_start = timezone.now() - timedelta(days=7)
        past_end = timezone.now() - timedelta(days=1)
        
        key = ActivationKey.objects.create(
            key="EXPIRED-KEY",
            bunker=self.bunker,
            valid_from=past_start,
            valid_until=past_end,
            is_active=True
        )
        
        self.assertFalse(key.is_valid_now())

    def test_is_valid_now_max_uses_reached(self):
        """Test is_valid_now returns False when max uses reached"""
        now = timezone.now()
        
        key = ActivationKey.objects.create(
            key="LIMITED-KEY",
            bunker=self.bunker,
            valid_from=now,
            is_active=True,
            max_uses=3,
            times_used=3
        )
        
        self.assertFalse(key.is_valid_now())

    def test_can_be_used_by_assigned_user(self):
        """Test can_be_used_by returns True for assigned user"""
        now = timezone.now()
        
        key = ActivationKey.objects.create(
            key="ASSIGNED-KEY",
            bunker=self.bunker,
            assigned_to=self.user,
            valid_from=now,
            is_active=True
        )
        
        self.assertTrue(key.can_be_used_by(self.user))

    def test_can_be_used_by_wrong_user(self):
        """Test can_be_used_by returns False for non-assigned user"""
        now = timezone.now()
        other_user = User.objects.create_user(
            email="other@test.com",
            callsign="OTH001",
            password="testpass"
        )
        
        key = ActivationKey.objects.create(
            key="ASSIGNED-KEY2",
            bunker=self.bunker,
            assigned_to=self.user,
            valid_from=now,
            is_active=True
        )
        
        self.assertFalse(key.can_be_used_by(other_user))

    def test_use_key_increments_counter(self):
        """Test use_key increments times_used"""
        now = timezone.now()
        
        key = ActivationKey.objects.create(
            key="USE-KEY",
            bunker=self.bunker,
            valid_from=now,
            is_active=True
        )
        
        self.assertEqual(key.times_used, 0)
        key.use_key()
        self.assertEqual(key.times_used, 1)
        key.use_key()
        self.assertEqual(key.times_used, 2)


class ActivationLogModelTest(TestCase):
    """Test ActivationLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="logger@test.com",
            callsign="LOG001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Test",
            name_en="Test"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-400",
            name_pl="Log Bunker",
            name_en="Log Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_activation_log_creation(self):
        """Test activation log is created correctly"""
        activation_time = timezone.now()
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=activation_time,
            qso_count=25,
            is_b2b=False,
            verified=False
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.bunker, self.bunker)
        self.assertEqual(log.qso_count, 25)
        self.assertFalse(log.is_b2b)
        self.assertFalse(log.verified)

    def test_activation_log_str_method(self):
        """Test __str__ returns formatted string"""
        activation_time = timezone.now()
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=activation_time
        )
        
        expected_date = activation_time.strftime('%Y-%m-%d')
        self.assertIn("LOG001", str(log))
        self.assertIn("BNK-400", str(log))
        self.assertIn(expected_date, str(log))

    def test_activation_log_with_key(self):
        """Test activation log can reference activation key"""
        now = timezone.now()
        
        key = ActivationKey.objects.create(
            key="LOG-KEY",
            bunker=self.bunker,
            valid_from=now,
            is_active=True
        )
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_key=key,
            activation_date=now
        )
        
        self.assertEqual(log.activation_key, key)

    def test_get_duration(self):
        """Test get_duration calculates correctly"""
        start = timezone.now()
        end = start + timedelta(hours=4)
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=start,
            end_date=end
        )
        
        duration = log.get_duration()
        self.assertIsNotNone(duration)
        self.assertEqual(duration, timedelta(hours=4))

    def test_get_duration_hours(self):
        """Test get_duration_hours returns hours as float"""
        start = timezone.now()
        end = start + timedelta(hours=3, minutes=30)
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=start,
            end_date=end
        )
        
        hours = log.get_duration_hours()
        self.assertAlmostEqual(hours, 3.5, places=1)

    def test_b2b_activation(self):
        """Test B2B activation flag"""
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=timezone.now(),
            is_b2b=True,
            qso_count=10
        )
        
        self.assertTrue(log.is_b2b)

    def test_verification_workflow(self):
        """Test activation verification"""
        verifier = User.objects.create_user(
            email="verifier@test.com",
            callsign="VER001",
            password="testpass"
        )
        
        log = ActivationLog.objects.create(
            user=self.user,
            bunker=self.bunker,
            activation_date=timezone.now(),
            verified=False
        )
        
        self.assertFalse(log.verified)
        self.assertIsNone(log.verified_by)
        
        # Verify
        log.verified = True
        log.verified_by = verifier
        log.save()
        
        self.assertTrue(log.verified)
        self.assertEqual(log.verified_by, verifier)


class LicenseModelTest(TestCase):
    """Test License model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="license@test.com",
            callsign="LIC001",
            password="testpass123"
        )
        self.issuer = User.objects.create_user(
            email="issuer@test.com",
            callsign="ISS001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Test",
            name_en="Test"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-500",
            name_pl="License Bunker",
            name_en="License Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_license_creation(self):
        """Test license is created correctly"""
        start = timezone.now()
        end = start + timedelta(days=30)
        
        license = License.objects.create(
            license_number="LIC-2025-001",
            license_type="contest",
            title_pl="Licencja Konkursowa",
            title_en="Contest License",
            issued_to=self.user,
            valid_from=start,
            valid_until=end,
            is_active=True,
            issued_by=self.issuer
        )
        
        self.assertEqual(license.license_number, "LIC-2025-001")
        self.assertEqual(license.license_type, "contest")
        self.assertEqual(license.issued_to, self.user)
        self.assertTrue(license.is_active)

    def test_license_str_method(self):
        """Test __str__ returns license number and title"""
        start = timezone.now()
        end = start + timedelta(days=30)
        
        license = License.objects.create(
            license_number="LIC-2025-002",
            license_type="special_event",
            title_pl="Wydarzenie Specjalne",
            title_en="Special Event",
            issued_to=self.user,
            valid_from=start,
            valid_until=end
        )
        
        expected = "LIC-2025-002 - Special Event"
        self.assertEqual(str(license), expected)

    def test_license_types(self):
        """Test all license types can be created"""
        types = ['contest', 'special_event', 'temporary', 'training', 'other']
        start = timezone.now()
        end = start + timedelta(days=30)
        
        for i, lic_type in enumerate(types):
            license = License.objects.create(
                license_number=f"LIC-{i}",
                license_type=lic_type,
                title_pl=f"Test {lic_type}",
                title_en=f"Test {lic_type}",
                issued_to=self.user,
                valid_from=start,
                valid_until=end
            )
            self.assertEqual(license.license_type, lic_type)

    def test_is_valid_now_active(self):
        """Test is_valid_now returns True for active license in date range"""
        now = timezone.now()
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)
        
        license = License.objects.create(
            license_number="LIC-VALID",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=past,
            valid_until=future,
            is_active=True
        )
        
        self.assertTrue(license.is_valid_now())

    def test_is_valid_now_inactive(self):
        """Test is_valid_now returns False for inactive license"""
        now = timezone.now()
        future = now + timedelta(days=1)
        
        license = License.objects.create(
            license_number="LIC-INACTIVE",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=now,
            valid_until=future,
            is_active=False
        )
        
        self.assertFalse(license.is_valid_now())

    def test_is_valid_now_expired(self):
        """Test is_valid_now returns False for expired license"""
        past_start = timezone.now() - timedelta(days=7)
        past_end = timezone.now() - timedelta(days=1)
        
        license = License.objects.create(
            license_number="LIC-EXPIRED",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=past_start,
            valid_until=past_end,
            is_active=True
        )
        
        self.assertFalse(license.is_valid_now())

    def test_is_valid_for_bunker_unrestricted(self):
        """Test is_valid_for_bunker returns True when no bunkers specified"""
        now = timezone.now()
        future = now + timedelta(days=1)
        
        license = License.objects.create(
            license_number="LIC-UNRESTRICTED",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=now,
            valid_until=future,
            is_active=True
        )
        
        self.assertTrue(license.is_valid_for_bunker(self.bunker))

    def test_is_valid_for_bunker_authorized(self):
        """Test is_valid_for_bunker returns True for authorized bunker"""
        now = timezone.now()
        future = now + timedelta(days=1)
        
        license = License.objects.create(
            license_number="LIC-RESTRICTED",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=now,
            valid_until=future,
            is_active=True
        )
        license.bunkers.add(self.bunker)
        
        self.assertTrue(license.is_valid_for_bunker(self.bunker))

    def test_is_valid_for_bunker_unauthorized(self):
        """Test is_valid_for_bunker returns False for unauthorized bunker"""
        now = timezone.now()
        future = now + timedelta(days=1)
        
        other_bunker = Bunker.objects.create(
            reference_number="BNK-501",
            name_pl="Other",
            name_en="Other",
            category=self.category,
            latitude=Decimal("53.0"),
            longitude=Decimal("22.0")
        )
        
        license = License.objects.create(
            license_number="LIC-RESTRICTED2",
            license_type="contest",
            title_pl="Test",
            title_en="Test",
            issued_to=self.user,
            valid_from=now,
            valid_until=future,
            is_active=True
        )
        license.bunkers.add(self.bunker)  # Only authorize self.bunker
        
        self.assertFalse(license.is_valid_for_bunker(other_bunker))
