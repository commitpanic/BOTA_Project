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
    
    # Integrity tracking for cache
    last_transaction_id = models.IntegerField(
        _('last transaction ID'),
        default=0,
        help_text=_('ID of last processed PointsTransaction')
    )
    last_recalculated = models.DateTimeField(
        _('last recalculated'),
        null=True,
        blank=True,
        help_text=_('When were statistics last recalculated from transactions')
    )

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
    
    def add_transaction(self, transaction):
        """
        Add points from a PointsTransaction to cached totals.
        Called automatically when transaction is created.
        
        Args:
            transaction: PointsTransaction instance
        """
        self.activator_points += transaction.activator_points
        self.hunter_points += transaction.hunter_points
        self.b2b_points += transaction.b2b_points
        self.event_points += transaction.event_points
        self.diploma_points += transaction.diploma_points
        
        self.update_total_points()
        self.last_transaction_id = transaction.id
        self.save()
    
    def recalculate_from_transactions(self):
        """
        Rebuild statistics from PointsTransaction table (source of truth).
        Use this to verify integrity or fix corrupted cache.
        """
        from django.db.models import Sum, Q
        # PointsTransaction is defined in this same file
        
        # Get all non-reversed transactions
        transactions = PointsTransaction.objects.filter(
            user=self.user,
            is_reversed=False
        )
        
        # Aggregate points
        agg = transactions.aggregate(
            activator=Sum('activator_points'),
            hunter=Sum('hunter_points'),
            b2b=Sum('b2b_points'),
            event=Sum('event_points'),
            diploma=Sum('diploma_points')
        )
        
        self.activator_points = agg['activator'] or 0
        self.hunter_points = agg['hunter'] or 0
        self.b2b_points = agg['b2b'] or 0
        self.event_points = agg['event'] or 0
        self.diploma_points = agg['diploma'] or 0
        
        # Recalculate QSO counts from ActivationLog
        from activations.models import ActivationLog
        
        self.total_activator_qso = ActivationLog.objects.filter(
            activator=self.user
        ).count()
        
        self.total_hunter_qso = ActivationLog.objects.filter(
            user=self.user
        ).exclude(activator=self.user).count()
        
        self.total_b2b_qso = ActivationLog.objects.filter(
            activator=self.user,
            is_b2b=True
        ).count()
        
        self.activator_b2b_qso = ActivationLog.objects.filter(
            activator=self.user,
            is_b2b=True,
            b2b_confirmed=True
        ).count()
        
        self.unique_activations = ActivationLog.objects.filter(
            activator=self.user
        ).values('bunker').distinct().count()
        
        self.unique_bunkers_hunted = ActivationLog.objects.filter(
            user=self.user
        ).exclude(activator=self.user).values('bunker').distinct().count()
        
        # Update metadata
        self.update_total_points()
        self.last_recalculated = timezone.now()
        
        # Get last transaction ID
        last_tx = transactions.order_by('-id').first()
        self.last_transaction_id = last_tx.id if last_tx else 0
        
        self.save()

    def add_hunter_qso(self, bunker_id=None):
        """
        Increment hunter statistics when user hunts a bunker.
        NOTE: Use PointsTransaction for actual point awarding!
        """
        self.total_hunter_qso += 1
        # Logic to check if bunker is unique would go here
        # For now, we'll just increment the counter
        self.save(update_fields=['total_hunter_qso', 'last_updated'])

    def add_activator_qso(self, bunker_id=None, is_b2b=False):
        """
        Increment activator statistics when user activates from a bunker.
        NOTE: Use PointsTransaction for actual point awarding!
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


# ============================================================================
# POINTS TRANSACTION SYSTEM - Event Sourcing
# ============================================================================

class PointsTransaction(models.Model):
    """
    Immutable history of all points awarded/deducted.
    Single source of truth for points system - all other tables are derived.
    
    Design principles:
    - Immutable: Once created, never modified (only reversed with new transaction)
    - Auditable: Full history of who got what points and why
    - Traceable: Links to context (ActivationLog, Diploma, etc.)
    - Reversible: Can be undone with reversal transaction
    """
    
    # Transaction types
    ACTIVATOR_QSO = 'activator_qso'
    HUNTER_QSO = 'hunter_qso'
    B2B_CONFIRMED = 'b2b_confirmed'
    B2B_CANCELLED = 'b2b_cancelled'
    DIPLOMA_BONUS = 'diploma_bonus'
    EVENT_BONUS = 'event_bonus'
    MANUAL_ADJUSTMENT = 'manual_adjustment'
    REVERSAL = 'reversal'
    
    TRANSACTION_TYPE_CHOICES = [
        (ACTIVATOR_QSO, _('Activator QSO')),
        (HUNTER_QSO, _('Hunter QSO')),
        (B2B_CONFIRMED, _('B2B Confirmed')),
        (B2B_CANCELLED, _('B2B Cancelled')),
        (DIPLOMA_BONUS, _('Diploma Bonus')),
        (EVENT_BONUS, _('Event Bonus')),
        (MANUAL_ADJUSTMENT, _('Manual Adjustment')),
        (REVERSAL, _('Reversal')),
    ]
    
    # Core fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='points_transactions',
        verbose_name=_('User'),
        db_index=True
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name=_('Transaction Type'),
        db_index=True
    )
    
    # Points breakdown (can be negative for reversals)
    activator_points = models.IntegerField(
        default=0,
        verbose_name=_('Activator Points')
    )
    hunter_points = models.IntegerField(
        default=0,
        verbose_name=_('Hunter Points')
    )
    b2b_points = models.IntegerField(
        default=0,
        verbose_name=_('B2B Points')
    )
    event_points = models.IntegerField(
        default=0,
        verbose_name=_('Event Points')
    )
    diploma_points = models.IntegerField(
        default=0,
        verbose_name=_('Diploma Points')
    )
    
    # Context - what triggered this transaction
    activation_log = models.ForeignKey(
        'activations.ActivationLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions',
        verbose_name=_('Activation Log')
    )
    bunker = models.ForeignKey(
        'bunkers.Bunker',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions',
        verbose_name=_('Bunker')
    )
    diploma = models.ForeignKey(
        'diplomas.Diploma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions',
        verbose_name=_('Diploma')
    )
    
    # Metadata
    reason = models.CharField(
        max_length=255,
        verbose_name=_('Reason'),
        help_text=_('Short description of why points were awarded')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Additional details or context')
    )
    
    # Audit trail
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_transactions',
        verbose_name=_('Created By'),
        help_text=_('User or system that created this transaction')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
        db_index=True
    )
    
    # Reversal linking
    reverses = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversed_by',
        verbose_name=_('Reverses Transaction'),
        help_text=_('If this is a reversal, which transaction does it reverse?')
    )
    is_reversed = models.BooleanField(
        default=False,
        verbose_name=_('Is Reversed'),
        help_text=_('Has this transaction been reversed?'),
        db_index=True
    )
    
    class Meta:
        verbose_name = _('Points Transaction')
        verbose_name_plural = _('Points Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['activation_log']),
        ]
    
    def __str__(self):
        points = []
        if self.activator_points:
            points.append(f'{self.activator_points:+d} ACT')
        if self.hunter_points:
            points.append(f'{self.hunter_points:+d} HNT')
        if self.b2b_points:
            points.append(f'{self.b2b_points:+d} B2B')
        points_str = ', '.join(points) if points else '0 pts'
        
        return f"{self.user.callsign}: {points_str} - {self.get_transaction_type_display()}"
    
    @property
    def total_points(self):
        """Calculate total points for this transaction"""
        return (
            self.activator_points +
            self.hunter_points +
            self.b2b_points +
            self.event_points +
            self.diploma_points
        )
    
    def reverse(self, reason, created_by=None):
        """
        Create a reversal transaction that undoes this one.
        
        Args:
            reason: Why is this being reversed?
            created_by: User performing the reversal
            
        Returns:
            PointsTransaction: The reversal transaction
        """
        if self.is_reversed:
            raise ValueError("This transaction has already been reversed")
        
        if self.transaction_type == self.REVERSAL:
            raise ValueError("Cannot reverse a reversal transaction")
        
        # Create reversal with negative points
        reversal = PointsTransaction.objects.create(
            user=self.user,
            transaction_type=self.REVERSAL,
            activator_points=-self.activator_points,
            hunter_points=-self.hunter_points,
            b2b_points=-self.b2b_points,
            event_points=-self.event_points,
            diploma_points=-self.diploma_points,
            activation_log=self.activation_log,
            bunker=self.bunker,
            diploma=self.diploma,
            reason=reason,
            notes=f"Reverses transaction #{self.id}: {self.reason}",
            created_by=created_by,
            reverses=self
        )
        
        # Mark original as reversed
        self.is_reversed = True
        self.save(update_fields=['is_reversed'])
        
        return reversal
    
    def save(self, *args, **kwargs):
        """Override save to update UserStatistics cache"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update the cached statistics
            stats, _ = UserStatistics.objects.get_or_create(user=self.user)
            stats.add_transaction(self)


class PointsTransactionBatch(models.Model):
    """
    Group of transactions processed together (e.g., from one log upload).
    Useful for bulk operations and rollbacks.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Batch Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Link to source
    log_upload = models.OneToOneField(
        'activations.LogUpload',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='points_batch',
        verbose_name=_('Log Upload')
    )
    
    transactions = models.ManyToManyField(
        PointsTransaction,
        related_name='batches',
        verbose_name=_('Transactions')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Reversal tracking
    is_reversed = models.BooleanField(
        default=False,
        verbose_name=_('Is Reversed')
    )
    reversed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Reversed At')
    )
    
    class Meta:
        verbose_name = _('Points Transaction Batch')
        verbose_name_plural = _('Points Transaction Batches')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.transactions.count()} transactions)"
    
    def reverse_all(self, reason, created_by=None):
        """Reverse all transactions in this batch"""
        if self.is_reversed:
            raise ValueError("This batch has already been reversed")
        
        reversal_transactions = []
        for transaction in self.transactions.filter(is_reversed=False):
            reversal = transaction.reverse(
                reason=f"{reason} (Batch reversal)",
                created_by=created_by
            )
            reversal_transactions.append(reversal)
        
        self.is_reversed = True
        self.reversed_at = timezone.now()
        self.save(update_fields=['is_reversed', 'reversed_at'])
        
        return reversal_transactions
