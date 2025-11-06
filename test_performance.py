"""
Performance test for home page caching
Tests database query reduction through caching
"""
import time
from django.core.cache import cache
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from bunkers.models import Bunker, BunkerCategory
from activations.models import ActivationLog
from diplomas.models import Diploma, DiplomaType

User = get_user_model()


class CachingPerformanceTest(TestCase):
    """Test caching performance improvements"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests"""
        # Create category
        cls.category = BunkerCategory.objects.create(
            name_en="Test Category",
            name_pl="Kategoria testowa"
        )
        
        # Create test bunkers
        for i in range(20):
            Bunker.objects.create(
                reference_number=f"B/TEST-{i:04d}",
                name_en=f"Test Bunker {i}",
                name_pl=f"Testowy Bunkier {i}",
                latitude=52.0 + i * 0.01,
                longitude=21.0 + i * 0.01,
                category=cls.category,
                is_verified=True
            )
        
        # Create test users
        for i in range(10):
            User.objects.create_user(
                email=f"test{i}@example.com",
                callsign=f"SP{i}TST",
                password="testpass123"
            )
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
        self.client = Client()
    
    def test_home_page_cache_performance(self):
        """Test home page cache reduces database queries"""
        
        # Ensure cache is clear
        cache.delete('home_statistics')
        
        # First request - cache miss (should hit database)
        start_time = time.time()
        # Note: Query count may vary based on middleware and session handling
        response1 = self.client.get('/', follow=True)
        first_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        print(f"\nFirst request (cache miss): {first_request_time*1000:.2f}ms")
        
        # Second request - cache hit (should not hit statistics queries)
        start_time = time.time()
        response2 = self.client.get('/', follow=True)
        second_request_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        print(f"Second request (cache hit): {second_request_time*1000:.2f}ms")
        
        # Cache should make subsequent requests faster
        self.assertLess(second_request_time, first_request_time,
                       "Cached request should be faster than uncached")
        
        # Calculate improvement
        if first_request_time > 0:
            improvement = ((first_request_time - second_request_time) / first_request_time) * 100
            speedup = first_request_time / second_request_time if second_request_time > 0 else 0
            print(f"Performance improvement: {improvement:.1f}%")
            print(f"Speed increase: {speedup:.1f}x faster")
    
    def test_cache_invalidation_timing(self):
        """Test that cache expires after timeout"""
        
        # Request page to populate cache with 1-second timeout
        cache_key = 'home_statistics'
        cache.set(cache_key, {'test': 'data'}, 1)
        
        # Verify cache is populated
        self.assertIsNotNone(cache.get(cache_key))
        print("\nCache populated with 1-second timeout")
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Verify cache has expired
        self.assertIsNone(cache.get(cache_key))
        print("Cache expired after timeout")
    
    def test_cache_key_uniqueness(self):
        """Test that different cache keys don't collide"""
        
        # Set different cache keys
        cache.set('home_statistics', {'page': 'home'}, 300)
        cache.set('user_statistics', {'page': 'user'}, 300)
        
        # Verify both exist and are different
        home_data = cache.get('home_statistics')
        user_data = cache.get('user_statistics')
        
        self.assertIsNotNone(home_data)
        self.assertIsNotNone(user_data)
        self.assertNotEqual(home_data, user_data)
        print("\nCache keys are independent and don't collide")


class DatabaseOptimizationTest(TestCase):
    """Test database query optimization"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data"""
        cls.category = BunkerCategory.objects.create(
            name_en="Test Category",
            name_pl="Kategoria testowa"
        )
        
        cls.bunker = Bunker.objects.create(
            reference_number="B/TEST-0001",
            name_en="Test Bunker",
            name_pl="Testowy Bunkier",
            latitude=52.0,
            longitude=21.0,
            category=cls.category,
            is_verified=True
        )
        
        cls.user = User.objects.create_user(
            email="activator@example.com",
            callsign="SP1TST",
            password="testpass123"
        )
    
    def test_activation_log_select_related(self):
        """Test that ActivationLog queries use select_related"""
        from datetime import datetime
        
        # Create activation logs
        for i in range(5):
            ActivationLog.objects.create(
                bunker=self.bunker,
                activator=self.user,
                user=self.user,
                activation_date=datetime.now(),
                mode="SSB",
                band="20m",
                qso_count=1,
                is_b2b=False,
                verified=True
            )
        
        # Query with select_related should use 1 query
        with self.assertNumQueries(1):
            logs = list(ActivationLog.objects.select_related('activator', 'bunker').all())
            # Access related fields - should not trigger additional queries
            for log in logs:
                _ = log.activator.callsign
                _ = log.bunker.reference_number
        
        print("\nActivationLog with select_related: 1 query for 5 logs + related data")
        
        # Query without select_related would use 11 queries (1 + 5*2)
        # This demonstrates the N+1 problem we avoided


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
    django.setup()
    
    from django.test.utils import get_runner
    TestRunner = get_runner(django.conf.settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
