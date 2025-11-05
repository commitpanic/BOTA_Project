from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    def create_user(self, email, callsign, password=None, **extra_fields):
        """
        Create and save a regular user with email and callsign.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not callsign:
            raise ValueError(_('The Callsign field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, callsign=callsign, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, callsign, password=None, **extra_fields):
        """
        Create and save a superuser with email and callsign.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, callsign, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the username field.
    Simplified to only email, password, and callsign for regular use.
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        help_text=_('Required. Email address used for authentication.')
    )
    callsign = models.CharField(
        _('callsign'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Required. Unique callsign/display name.')
    )
    
    # System fields
    auto_created = models.BooleanField(
        _('auto created'),
        default=False,
        help_text=_('True if user was automatically created from log import, not manually registered.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.')
    )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_('Designates that this user has all permissions.')
    )
    
    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    # Security fields
    force_password_change = models.BooleanField(
        _('force password change'),
        default=False,
        help_text=_('User must change password on next login')
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['callsign']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['callsign']),
        ]

    def __str__(self):
        return f"{self.callsign} ({self.email})"

    def get_full_name(self):
        """Return the callsign as the full name."""
        return self.callsign

    def get_short_name(self):
        """Return the callsign as the short name."""
        return self.callsign


class UserStatistics(models.Model):
    """
    Track user activity statistics for diploma achievements.
    OneToOne relationship with User - automatically created for each user.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='statistics',
        verbose_name=_('user')
    )
    
    # Activator Statistics
    total_activator_qso = models.PositiveIntegerField(
        _('total activator QSO'),
        default=0,
        help_text=_('Total QSOs from bunkers as activator')
    )
    unique_activations = models.PositiveIntegerField(
        _('unique activations'),
        default=0,
        help_text=_('Number of unique bunkers activated')
    )
    activator_b2b_qso = models.PositiveIntegerField(
        _('activator B2B QSO'),
        default=0,
        help_text=_('Bunker-to-Bunker QSOs as activator')
    )
    
    # Hunter Statistics
    total_hunter_qso = models.PositiveIntegerField(
        _('total hunter QSO'),
        default=0,
        help_text=_('Total hunted QSOs')
    )
    unique_bunkers_hunted = models.PositiveIntegerField(
        _('unique bunkers hunted'),
        default=0,
        help_text=_('Number of unique bunkers hunted')
    )
    
    # General Statistics
    total_b2b_qso = models.PositiveIntegerField(
        _('total B2B QSO'),
        default=0,
        help_text=_('Total Bunker-to-Bunker connections')
    )
    
    # Points System
    total_points = models.PositiveIntegerField(
        _('total points'),
        default=0,
        help_text=_('Total points earned from all activities')
    )
    hunter_points = models.PositiveIntegerField(
        _('hunter points'),
        default=0,
        help_text=_('Points earned from hunting activities')
    )
    activator_points = models.PositiveIntegerField(
        _('activator points'),
        default=0,
        help_text=_('Points earned from activating bunkers')
    )
    b2b_points = models.PositiveIntegerField(
        _('B2B points'),
        default=0,
        help_text=_('Points earned from B2B connections')
    )
    event_points = models.PositiveIntegerField(
        _('event points'),
        default=0,
        help_text=_('Points earned from special events')
    )
    diploma_points = models.PositiveIntegerField(
        _('diploma points'),
        default=0,
        help_text=_('Points earned from earning diplomas')
    )
    
    # Timestamps
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('user statistics')
        verbose_name_plural = _('user statistics')
        ordering = ['-total_points']

    def __str__(self):
        return f"Statistics for {self.user.callsign}"

    def update_total_points(self):
        """
        Recalculate total points from all point categories.
        """
        self.total_points = (
            self.hunter_points +
            self.activator_points +
            self.b2b_points +
            self.event_points +
            self.diploma_points
        )
        self.save(update_fields=['total_points', 'last_updated'])

    def add_hunter_qso(self, bunker_id=None):
        """
        Increment hunter statistics when user hunts a bunker.
        """
        self.total_hunter_qso += 1
        # Logic to check if bunker is unique would go here
        # For now, we'll just increment the counter
        self.save(update_fields=['total_hunter_qso', 'last_updated'])

    def add_activator_qso(self, bunker_id=None, is_b2b=False):
        """
        Increment activator statistics when user activates from a bunker.
        """
        self.total_activator_qso += 1
        if is_b2b:
            self.activator_b2b_qso += 1
            self.total_b2b_qso += 1
        # Logic to check if bunker is unique would go here
        self.save(update_fields=[
            'total_activator_qso', 
            'activator_b2b_qso', 
            'total_b2b_qso',
            'last_updated'
        ])


class UserRole(models.Model):
    """
    Define user roles for role-based access control (RBAC).
    """
    name = models.CharField(
        _('role name'),
        max_length=50,
        unique=True,
        help_text=_('Unique role name (e.g., Admin, Manager, Operator)')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the role and its permissions')
    )
    permissions = models.JSONField(
        _('permissions'),
        default=dict,
        help_text=_('Custom permissions dictionary for this role')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        ordering = ['name']

    def __str__(self):
        return self.name


class UserRoleAssignment(models.Model):
    """
    Assign roles to users (Many-to-Many through model).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments',
        verbose_name=_('user')
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='user_assignments',
        verbose_name=_('role')
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles',
        verbose_name=_('assigned by')
    )
    assigned_at = models.DateTimeField(_('assigned at'), auto_now_add=True)
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this role assignment is currently active')
    )

    class Meta:
        verbose_name = _('user role assignment')
        verbose_name_plural = _('user role assignments')
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.callsign} - {self.role.name}"
