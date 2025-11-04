from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from accounts.models import UserStatistics, UserRole, UserRoleAssignment

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for the custom User model.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.user_data = {
            'email': 'test@example.com',
            'callsign': 'TEST123',
            'password': 'securepassword123'
        }

    def test_create_user_with_email_and_callsign(self):
        """
        Test creating a user with email and callsign.
        """
        user = User.objects.create_user(
            email=self.user_data['email'],
            callsign=self.user_data['callsign'],
            password=self.user_data['password']
        )
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.callsign, self.user_data['callsign'])
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_create_superuser(self):
        """
        Test creating a superuser.
        """
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            callsign='ADMIN',
            password='adminpass123'
        )
        
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_email_is_unique(self):
        """
        Test that email must be unique.
        """
        User.objects.create_user(
            email='test@example.com',
            callsign='USER1',
            password='pass123'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',
                callsign='USER2',
                password='pass456'
            )

    def test_user_callsign_is_unique(self):
        """
        Test that callsign must be unique.
        """
        User.objects.create_user(
            email='user1@example.com',
            callsign='TEST123',
            password='pass123'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='user2@example.com',
                callsign='TEST123',
                password='pass456'
            )

    def test_user_email_normalization(self):
        """
        Test that email is normalized (lowercased domain).
        """
        user = User.objects.create_user(
            email='test@EXAMPLE.COM',
            callsign='TEST123',
            password='pass123'
        )
        
        self.assertEqual(user.email, 'test@example.com')

    def test_user_without_email_raises_error(self):
        """
        Test that creating user without email raises ValueError.
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                callsign='TEST123',
                password='pass123'
            )

    def test_user_without_callsign_raises_error(self):
        """
        Test that creating user without callsign raises ValueError.
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='test@example.com',
                callsign='',
                password='pass123'
            )

    def test_user_string_representation(self):
        """
        Test the string representation of User.
        """
        user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST123',
            password='pass123'
        )
        
        self.assertEqual(str(user), 'TEST123 (test@example.com)')

    def test_user_get_full_name(self):
        """
        Test get_full_name returns callsign.
        """
        user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST123',
            password='pass123'
        )
        
        self.assertEqual(user.get_full_name(), 'TEST123')

    def test_user_get_short_name(self):
        """
        Test get_short_name returns callsign.
        """
        user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST123',
            password='pass123'
        )
        
        self.assertEqual(user.get_short_name(), 'TEST123')


class UserStatisticsModelTest(TestCase):
    """
    Test cases for the UserStatistics model.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST123',
            password='pass123'
        )

    def test_user_statistics_auto_created(self):
        """
        Test that UserStatistics is automatically created for new user.
        """
        self.assertTrue(hasattr(self.user, 'statistics'))
        self.assertIsInstance(self.user.statistics, UserStatistics)

    def test_user_statistics_initial_values(self):
        """
        Test that UserStatistics has correct initial values.
        """
        stats = self.user.statistics
        
        self.assertEqual(stats.total_activator_qso, 0)
        self.assertEqual(stats.unique_activations, 0)
        self.assertEqual(stats.activator_b2b_qso, 0)
        self.assertEqual(stats.total_hunter_qso, 0)
        self.assertEqual(stats.unique_bunkers_hunted, 0)
        self.assertEqual(stats.total_b2b_qso, 0)
        self.assertEqual(stats.total_points, 0)
        self.assertEqual(stats.hunter_points, 0)
        self.assertEqual(stats.activator_points, 0)
        self.assertEqual(stats.b2b_points, 0)
        self.assertEqual(stats.event_points, 0)
        self.assertEqual(stats.diploma_points, 0)

    def test_add_hunter_qso(self):
        """
        Test adding hunter QSO increments counter.
        """
        stats = self.user.statistics
        initial_count = stats.total_hunter_qso
        
        stats.add_hunter_qso()
        stats.refresh_from_db()
        
        self.assertEqual(stats.total_hunter_qso, initial_count + 1)

    def test_add_activator_qso(self):
        """
        Test adding activator QSO increments counter.
        """
        stats = self.user.statistics
        initial_count = stats.total_activator_qso
        
        stats.add_activator_qso()
        stats.refresh_from_db()
        
        self.assertEqual(stats.total_activator_qso, initial_count + 1)

    def test_add_activator_qso_b2b(self):
        """
        Test adding B2B activator QSO increments multiple counters.
        """
        stats = self.user.statistics
        
        stats.add_activator_qso(is_b2b=True)
        stats.refresh_from_db()
        
        self.assertEqual(stats.total_activator_qso, 1)
        self.assertEqual(stats.activator_b2b_qso, 1)
        self.assertEqual(stats.total_b2b_qso, 1)

    def test_update_total_points(self):
        """
        Test that update_total_points recalculates total correctly.
        """
        stats = self.user.statistics
        
        stats.hunter_points = 100
        stats.activator_points = 200
        stats.b2b_points = 50
        stats.event_points = 75
        stats.diploma_points = 25
        stats.save()
        
        stats.update_total_points()
        stats.refresh_from_db()
        
        self.assertEqual(stats.total_points, 450)

    def test_user_statistics_string_representation(self):
        """
        Test the string representation of UserStatistics.
        """
        stats = self.user.statistics
        self.assertEqual(str(stats), 'Statistics for TEST123')


class UserRoleModelTest(TestCase):
    """
    Test cases for the UserRole model.
    """

    def test_create_user_role(self):
        """
        Test creating a user role.
        """
        role = UserRole.objects.create(
            name='Admin',
            description='Administrator role with full permissions',
            permissions={'can_manage_users': True, 'can_delete_bunkers': True}
        )
        
        self.assertEqual(role.name, 'Admin')
        self.assertEqual(role.description, 'Administrator role with full permissions')
        self.assertIsInstance(role.permissions, dict)
        self.assertTrue(role.permissions['can_manage_users'])

    def test_user_role_name_is_unique(self):
        """
        Test that role name must be unique.
        """
        UserRole.objects.create(name='Admin', description='Test')
        
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(name='Admin', description='Another')

    def test_user_role_string_representation(self):
        """
        Test the string representation of UserRole.
        """
        role = UserRole.objects.create(name='Manager')
        self.assertEqual(str(role), 'Manager')


class UserRoleAssignmentModelTest(TestCase):
    """
    Test cases for the UserRoleAssignment model.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            callsign='TEST123',
            password='pass123'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            callsign='ADMIN',
            password='admin123'
        )
        self.role = UserRole.objects.create(
            name='Manager',
            description='Manager role'
        )

    def test_assign_role_to_user(self):
        """
        Test assigning a role to a user.
        """
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin
        )
        
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.role, self.role)
        self.assertEqual(assignment.assigned_by, self.admin)
        self.assertTrue(assignment.is_active)

    def test_user_role_assignment_unique_together(self):
        """
        Test that user-role combination must be unique.
        """
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin
        )
        
        with self.assertRaises(IntegrityError):
            UserRoleAssignment.objects.create(
                user=self.user,
                role=self.role,
                assigned_by=self.admin
            )

    def test_user_role_assignment_string_representation(self):
        """
        Test the string representation of UserRoleAssignment.
        """
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin
        )
        
        self.assertEqual(str(assignment), 'TEST123 - Manager')

    def test_deactivate_role_assignment(self):
        """
        Test deactivating a role assignment.
        """
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin
        )
        
        assignment.is_active = False
        assignment.save()
        
        self.assertFalse(assignment.is_active)
