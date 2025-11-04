from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Cluster, ClusterMember, ClusterAlert
from bunkers.models import Bunker, BunkerCategory

User = get_user_model()


class ClusterModelTest(TestCase):
    """Test Cluster model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cluster_admin@test.com",
            callsign="CLU001",
            password="testpass123"
        )
        self.cluster = Cluster.objects.create(
            name_pl="Linia Mołotowa",
            name_en="Molotov Line",
            description_pl="System fortyfikacji",
            description_en="Fortification system",
            region="Lubelskie",
            created_by=self.user,
            is_active=True
        )

    def test_cluster_creation(self):
        """Test cluster is created correctly"""
        self.assertEqual(self.cluster.name_pl, "Linia Mołotowa")
        self.assertEqual(self.cluster.name_en, "Molotov Line")
        self.assertEqual(self.cluster.region, "Lubelskie")
        self.assertTrue(self.cluster.is_active)
        self.assertEqual(self.cluster.created_by, self.user)
        self.assertIsNotNone(self.cluster.created_at)

    def test_cluster_str_method(self):
        """Test __str__ returns bilingual name"""
        expected = "Molotov Line / Linia Mołotowa"
        self.assertEqual(str(self.cluster), expected)

    def test_cluster_ordering(self):
        """Test clusters are ordered by region then name_en"""
        cluster2 = Cluster.objects.create(
            name_pl="Fortyfikacje Gdańskie",
            name_en="Gdańsk Fortifications",
            region="Pomorskie"
        )
        cluster3 = Cluster.objects.create(
            name_pl="Forty Modlińskie",
            name_en="Modlin Fortifications",
            region="Mazowieckie"
        )
        
        clusters = list(Cluster.objects.all())
        # Alphabetically by region: Lubelskie, Mazowieckie, Pomorskie
        self.assertEqual(clusters[0].region, "Lubelskie")
        self.assertEqual(clusters[1].region, "Mazowieckie")
        self.assertEqual(clusters[2].region, "Pomorskie")

    def test_get_bunker_count_empty(self):
        """Test get_bunker_count returns 0 for cluster with no bunkers"""
        self.assertEqual(self.cluster.get_bunker_count(), 0)

    def test_get_bunker_count_with_bunkers(self):
        """Test get_bunker_count returns correct count"""
        category = BunkerCategory.objects.create(
            name_pl="Test",
            name_en="Test"
        )
        bunker1 = Bunker.objects.create(
            reference_number="BNK-100",
            name_pl="Bunkier 1",
            name_en="Bunker 1",
            category=category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )
        bunker2 = Bunker.objects.create(
            reference_number="BNK-101",
            name_pl="Bunkier 2",
            name_en="Bunker 2",
            category=category,
            latitude=Decimal("52.1"),
            longitude=Decimal("21.1")
        )
        
        ClusterMember.objects.create(cluster=self.cluster, bunker=bunker1)
        ClusterMember.objects.create(cluster=self.cluster, bunker=bunker2)
        
        self.assertEqual(self.cluster.get_bunker_count(), 2)

    def test_get_active_bunkers(self):
        """Test get_active_bunkers returns only verified bunkers"""
        category = BunkerCategory.objects.create(
            name_pl="Test",
            name_en="Test"
        )
        bunker1 = Bunker.objects.create(
            reference_number="BNK-102",
            name_pl="Verified",
            name_en="Verified",
            category=category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0"),
            is_verified=True
        )
        bunker2 = Bunker.objects.create(
            reference_number="BNK-103",
            name_pl="Not Verified",
            name_en="Not Verified",
            category=category,
            latitude=Decimal("52.1"),
            longitude=Decimal("21.1"),
            is_verified=False
        )
        
        ClusterMember.objects.create(cluster=self.cluster, bunker=bunker1)
        ClusterMember.objects.create(cluster=self.cluster, bunker=bunker2)
        
        active = self.cluster.get_active_bunkers()
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().bunker.reference_number, "BNK-102")


class ClusterMemberModelTest(TestCase):
    """Test ClusterMember model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="member_admin@test.com",
            callsign="MEM001",
            password="testpass123"
        )
        self.cluster = Cluster.objects.create(
            name_pl="Test Cluster",
            name_en="Test Cluster"
        )
        self.category = BunkerCategory.objects.create(
            name_pl="Kategoria",
            name_en="Category"
        )
        self.bunker = Bunker.objects.create(
            reference_number="BNK-200",
            name_pl="Test Bunkier",
            name_en="Test Bunker",
            category=self.category,
            latitude=Decimal("52.0"),
            longitude=Decimal("21.0")
        )

    def test_cluster_member_creation(self):
        """Test cluster member is created correctly"""
        member = ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker,
            display_order=1,
            notes="Main bunker of the cluster",
            added_by=self.user
        )
        
        self.assertEqual(member.cluster, self.cluster)
        self.assertEqual(member.bunker, self.bunker)
        self.assertEqual(member.display_order, 1)
        self.assertEqual(member.added_by, self.user)
        self.assertIsNotNone(member.join_date)

    def test_cluster_member_str_method(self):
        """Test __str__ returns bunker reference and cluster name"""
        member = ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker
        )
        expected = "BNK-200 in Test Cluster"
        self.assertEqual(str(member), expected)

    def test_cluster_member_unique_together(self):
        """Test same bunker can't be added to same cluster twice"""
        ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker
        )
        
        with self.assertRaises(Exception):
            ClusterMember.objects.create(
                cluster=self.cluster,
                bunker=self.bunker
            )

    def test_cluster_member_ordering(self):
        """Test cluster members are ordered by display_order"""
        bunker2 = Bunker.objects.create(
            reference_number="BNK-201",
            name_pl="Bunkier 2",
            name_en="Bunker 2",
            category=self.category,
            latitude=Decimal("52.1"),
            longitude=Decimal("21.1")
        )
        bunker3 = Bunker.objects.create(
            reference_number="BNK-202",
            name_pl="Bunkier 3",
            name_en="Bunker 3",
            category=self.category,
            latitude=Decimal("52.2"),
            longitude=Decimal("21.2")
        )
        
        ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=bunker2,
            display_order=2
        )
        ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker,
            display_order=1
        )
        ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=bunker3,
            display_order=3
        )
        
        members = list(ClusterMember.objects.filter(cluster=self.cluster))
        self.assertEqual(members[0].bunker.reference_number, "BNK-200")
        self.assertEqual(members[1].bunker.reference_number, "BNK-201")
        self.assertEqual(members[2].bunker.reference_number, "BNK-202")

    def test_bunker_can_belong_to_multiple_clusters(self):
        """Test a bunker can be member of multiple clusters"""
        cluster2 = Cluster.objects.create(
            name_pl="Drugi Cluster",
            name_en="Second Cluster"
        )
        
        member1 = ClusterMember.objects.create(
            cluster=self.cluster,
            bunker=self.bunker
        )
        member2 = ClusterMember.objects.create(
            cluster=cluster2,
            bunker=self.bunker
        )
        
        self.assertNotEqual(member1.pk, member2.pk)
        self.assertEqual(self.bunker.cluster_memberships.count(), 2)


class ClusterAlertModelTest(TestCase):
    """Test ClusterAlert model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="alert_admin@test.com",
            callsign="ALT001",
            password="testpass123"
        )
        self.cluster = Cluster.objects.create(
            name_pl="Test Cluster",
            name_en="Test Cluster"
        )

    def test_cluster_alert_creation(self):
        """Test cluster alert is created correctly"""
        start = timezone.now()
        end = start + timedelta(days=7)
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Specjalna Aktywacja",
            title_en="Special Activation",
            message_pl="Aktywacja w ten weekend",
            message_en="Activation this weekend",
            alert_type="special",
            is_active=True,
            start_date=start,
            end_date=end,
            created_by=self.user
        )
        
        self.assertEqual(alert.cluster, self.cluster)
        self.assertEqual(alert.title_en, "Special Activation")
        self.assertEqual(alert.alert_type, "special")
        self.assertTrue(alert.is_active)
        self.assertEqual(alert.created_by, self.user)

    def test_cluster_alert_str_method(self):
        """Test __str__ returns type, title and cluster"""
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Test",
            title_en="Test Alert",
            message_pl="Test",
            message_en="Test message",
            alert_type="info",
            start_date=timezone.now()
        )
        expected = "INFO: Test Alert (Test Cluster)"
        self.assertEqual(str(alert), expected)

    def test_alert_types(self):
        """Test all alert types can be created"""
        types = ['info', 'event', 'warning', 'special']
        start = timezone.now()
        
        for alert_type in types:
            alert = ClusterAlert.objects.create(
                cluster=self.cluster,
                title_pl=f"Test {alert_type}",
                title_en=f"Test {alert_type}",
                message_pl="Test",
                message_en="Test",
                alert_type=alert_type,
                start_date=start
            )
            self.assertEqual(alert.alert_type, alert_type)

    def test_is_currently_active_true(self):
        """Test is_currently_active returns True for active alert in date range"""
        now = timezone.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Aktywny",
            title_en="Active",
            message_pl="Test",
            message_en="Test",
            is_active=True,
            start_date=start,
            end_date=end
        )
        
        self.assertTrue(alert.is_currently_active())

    def test_is_currently_active_false_not_started(self):
        """Test is_currently_active returns False for future alert"""
        future = timezone.now() + timedelta(days=1)
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Przyszły",
            title_en="Future",
            message_pl="Test",
            message_en="Test",
            is_active=True,
            start_date=future
        )
        
        self.assertFalse(alert.is_currently_active())

    def test_is_currently_active_false_ended(self):
        """Test is_currently_active returns False for past alert"""
        past_start = timezone.now() - timedelta(days=7)
        past_end = timezone.now() - timedelta(days=1)
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Przeszły",
            title_en="Past",
            message_pl="Test",
            message_en="Test",
            is_active=True,
            start_date=past_start,
            end_date=past_end
        )
        
        self.assertFalse(alert.is_currently_active())

    def test_is_currently_active_false_inactive(self):
        """Test is_currently_active returns False when is_active=False"""
        now = timezone.now()
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Nieaktywny",
            title_en="Inactive",
            message_pl="Test",
            message_en="Test",
            is_active=False,
            start_date=now
        )
        
        self.assertFalse(alert.is_currently_active())

    def test_alert_without_end_date(self):
        """Test alert without end_date remains active"""
        past = timezone.now() - timedelta(days=1)
        
        alert = ClusterAlert.objects.create(
            cluster=self.cluster,
            title_pl="Bez końca",
            title_en="No end date",
            message_pl="Test",
            message_en="Test",
            is_active=True,
            start_date=past,
            end_date=None
        )
        
        self.assertTrue(alert.is_currently_active())
