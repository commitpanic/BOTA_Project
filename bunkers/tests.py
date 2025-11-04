from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import (
    BunkerCategory,
    Bunker,
    BunkerPhoto,
    BunkerResource,
    BunkerInspection
)

User = get_user_model()


class BunkerCategoryModelTest(TestCase):
    """Test BunkerCategory model"""

    def setUp(self):
        self.category = BunkerCategory.objects.create(
            name_pl="Bunkier Dowodzenia",
            name_en="Command Bunker",
            description_pl="Główny bunkier dowodzenia",
            description_en="Main command bunker",
            icon="fas fa-shield-alt",
            display_order=1
        )

    def test_category_creation(self):
        """Test that category is created correctly"""
        self.assertEqual(self.category.name_pl, "Bunkier Dowodzenia")
        self.assertEqual(self.category.name_en, "Command Bunker")
        self.assertEqual(self.category.display_order, 1)
        self.assertIsNotNone(self.category.created_at)
        self.assertIsNotNone(self.category.updated_at)

    def test_category_str_method(self):
        """Test __str__ returns bilingual name"""
        expected = "Command Bunker / Bunkier Dowodzenia"
        self.assertEqual(str(self.category), expected)

    def test_category_ordering(self):
        """Test categories are ordered by display_order then name_en"""
        cat2 = BunkerCategory.objects.create(
            name_pl="Bunkier Magazynowy",
            name_en="Storage Bunker",
            display_order=2
        )
        cat3 = BunkerCategory.objects.create(
            name_pl="Schron",
            name_en="Shelter",
            display_order=1
        )
        categories = list(BunkerCategory.objects.all())
        # Both have display_order=1, so alphabetically: Command < Shelter
        self.assertEqual(categories[0].name_en, "Command Bunker")
        self.assertEqual(categories[1].name_en, "Shelter")
        self.assertEqual(categories[2].name_en, "Storage Bunker")


class BunkerModelTest(TestCase):
    """Test Bunker model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="hunter@test.com",
            callsign="HNT001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Bunkier Testowy",
            name_en="Test Bunker"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-001",
            name_pl="Bunkier Westerplatte",
            name_en="Westerplatte Bunker",
            description_pl="Historyczny bunkier",
            description_en="Historical bunker",
            category=self.category,
            latitude=Decimal("54.403844"),
            longitude=Decimal("18.668472"),
            created_by=self.user
        )

    def test_bunker_creation(self):
        """Test bunker is created correctly"""
        self.assertEqual(self.bunker.reference_number, "BNK-001")
        self.assertEqual(self.bunker.name_en, "Westerplatte Bunker")
        self.assertEqual(self.bunker.category, self.category)
        self.assertEqual(self.bunker.latitude, Decimal("54.403844"))
        self.assertEqual(self.bunker.longitude, Decimal("18.668472"))
        self.assertFalse(self.bunker.is_verified)
        self.assertEqual(self.bunker.created_by, self.user)

    def test_bunker_str_method(self):
        """Test __str__ returns reference number and name"""
        expected = "BNK-001 - Westerplatte Bunker"
        self.assertEqual(str(self.bunker), expected)

    def test_bunker_reference_number_unique(self):
        """Test reference numbers must be unique"""
        with self.assertRaises(Exception):
            Bunker.objects.create(
                reference_number="BNK-001",  # Duplicate
                name_pl="Inny Bunkier",
                name_en="Another Bunker",
                category=self.category,
                latitude=Decimal("50.0"),
                longitude=Decimal("19.0")
            )

    def test_bunker_get_coordinates(self):
        """Test get_coordinates returns tuple"""
        coords = self.bunker.get_coordinates()
        self.assertEqual(coords, (54.403844, 18.668472))
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)

    def test_bunker_verification(self):
        """Test bunker verification workflow"""
        admin = User.objects.create_user(
            email="admin@test.com",
            callsign="ADMIN",
            password="adminpass"
        )
        self.assertFalse(self.bunker.is_verified)
        self.assertIsNone(self.bunker.verified_by)
        
        # Verify the bunker
        self.bunker.is_verified = True
        self.bunker.verified_by = admin
        self.bunker.verification_date = timezone.now()
        self.bunker.save()
        
        self.assertTrue(self.bunker.is_verified)
        self.assertEqual(self.bunker.verified_by, admin)
        self.assertIsNotNone(self.bunker.verification_date)

    def test_bunker_latitude_validation(self):
        """Test latitude must be between -90 and 90"""
        bunker = Bunker(
            reference_number="BNK-999",
            name_pl="Test",
            name_en="Test",
            category=self.category,
            latitude=Decimal("91.0"),  # Invalid
            longitude=Decimal("18.0")
        )
        with self.assertRaises(ValidationError):
            bunker.full_clean()

    def test_bunker_longitude_validation(self):
        """Test longitude must be between -180 and 180"""
        bunker = Bunker(
            reference_number="BNK-998",
            name_pl="Test",
            name_en="Test",
            category=self.category,
            latitude=Decimal("54.0"),
            longitude=Decimal("181.0")  # Invalid
        )
        with self.assertRaises(ValidationError):
            bunker.full_clean()


class BunkerPhotoModelTest(TestCase):
    """Test BunkerPhoto model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="photographer@test.com",
            callsign="PHT001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Kategoria",
            name_en="Category"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-002",
            name_pl="Bunkier",
            name_en="Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_photo_creation(self):
        """Test photo is created correctly"""
        photo = BunkerPhoto.objects.create(
            bunker=self.bunker,
            photo="bunker_photos/2025/11/test.jpg",
            caption_pl="Widok z przodu",
            caption_en="Front view",
            uploaded_by=self.user
        )
        self.assertEqual(photo.bunker, self.bunker)
        self.assertEqual(photo.caption_en, "Front view")
        self.assertFalse(photo.is_approved)
        self.assertIsNone(photo.approved_by)
        self.assertEqual(photo.uploaded_by, self.user)

    def test_photo_approval_workflow(self):
        """Test photo approval process"""
        photo = BunkerPhoto.objects.create(
            bunker=self.bunker,
            photo="bunker_photos/test.jpg",
            uploaded_by=self.user
        )
        moderator = User.objects.create_user(
            email="mod@test.com",
            callsign="MOD",
            password="modpass"
        )
        
        # Initially not approved
        self.assertFalse(photo.is_approved)
        
        # Approve photo
        photo.is_approved = True
        photo.approved_by = moderator
        photo.approval_date = timezone.now()
        photo.save()
        
        self.assertTrue(photo.is_approved)
        self.assertEqual(photo.approved_by, moderator)
        self.assertIsNotNone(photo.approval_date)

    def test_photo_str_method(self):
        """Test __str__ shows approval status"""
        photo = BunkerPhoto.objects.create(
            bunker=self.bunker,
            photo="test.jpg",
            uploaded_by=self.user
        )
        self.assertIn("⏳", str(photo))  # Pending
        self.assertIn("BNK-002", str(photo))
        
        photo.is_approved = True
        photo.save()
        self.assertIn("✓", str(photo))  # Approved


class BunkerResourceModelTest(TestCase):
    """Test BunkerResource model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="resource@test.com",
            callsign="RES001",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Kategoria",
            name_en="Category"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-003",
            name_pl="Bunkier",
            name_en="Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_resource_creation(self):
        """Test resource is created correctly"""
        resource = BunkerResource.objects.create(
            bunker=self.bunker,
            title_pl="Artykuł o bunkrze",
            title_en="Article about bunker",
            url="https://example.com/article",
            resource_type="article",
            added_by=self.user
        )
        self.assertEqual(resource.bunker, self.bunker)
        self.assertEqual(resource.title_en, "Article about bunker")
        self.assertEqual(resource.url, "https://example.com/article")
        self.assertEqual(resource.resource_type, "article")
        self.assertEqual(resource.added_by, self.user)

    def test_resource_types(self):
        """Test different resource types"""
        types = ['article', 'video', 'map', 'documentation', 'other']
        for res_type in types:
            resource = BunkerResource.objects.create(
                bunker=self.bunker,
                title_pl=f"Test {res_type}",
                title_en=f"Test {res_type}",
                url=f"https://example.com/{res_type}",
                resource_type=res_type,
                added_by=self.user
            )
            self.assertEqual(resource.resource_type, res_type)

    def test_resource_str_method(self):
        """Test __str__ returns title and reference"""
        resource = BunkerResource.objects.create(
            bunker=self.bunker,
            title_pl="Test",
            title_en="Test Resource",
            url="https://example.com",
            added_by=self.user
        )
        expected = "Test Resource (BNK-003)"
        self.assertEqual(str(resource), expected)


class BunkerInspectionModelTest(TestCase):
    """Test BunkerInspection model"""

    def setUp(self):
        self.hunter = User.objects.create_user(
            email="hunter@test.com",
            callsign="HNT002",
            password="testpass123"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Kategoria",
            name_en="Category"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-004",
            name_pl="Bunkier",
            name_en="Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_inspection_creation(self):
        """Test inspection is created correctly"""
        inspection_time = timezone.now()
        inspection = BunkerInspection.objects.create(
            bunker=self.bunker,
            user=self.hunter,
            inspection_date=inspection_time,
            notes="Found the bunker in good condition",
            verified=True
        )
        self.assertEqual(inspection.bunker, self.bunker)
        self.assertEqual(inspection.user, self.hunter)
        self.assertEqual(inspection.inspection_date, inspection_time)
        self.assertTrue(inspection.verified)

    def test_inspection_str_method(self):
        """Test __str__ returns user callsign and bunker reference"""
        inspection = BunkerInspection.objects.create(
            bunker=self.bunker,
            user=self.hunter,
            inspection_date=timezone.now()
        )
        expected = "HNT002 inspected BNK-004"
        self.assertEqual(str(inspection), expected)

    def test_inspection_unique_together(self):
        """Test same user can't inspect same bunker at same time"""
        inspection_time = timezone.now()
        BunkerInspection.objects.create(
            bunker=self.bunker,
            user=self.hunter,
            inspection_date=inspection_time
        )
        # Try to create duplicate
        with self.assertRaises(Exception):
            BunkerInspection.objects.create(
                bunker=self.bunker,
                user=self.hunter,
                inspection_date=inspection_time
            )

    def test_multiple_inspections_different_times(self):
        """Test user can inspect same bunker at different times"""
        time1 = timezone.now()
        time2 = timezone.now() + timezone.timedelta(hours=1)
        
        inspection1 = BunkerInspection.objects.create(
            bunker=self.bunker,
            user=self.hunter,
            inspection_date=time1
        )
        inspection2 = BunkerInspection.objects.create(
            bunker=self.bunker,
            user=self.hunter,
            inspection_date=time2
        )
        
        self.assertNotEqual(inspection1.pk, inspection2.pk)
        self.assertEqual(BunkerInspection.objects.filter(
            bunker=self.bunker,
            user=self.hunter
        ).count(), 2)
