from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import secrets
import string


class ActivationKey(models.Model):
    """
    Activation keys for bunkers. Users receive keys to activate bunkers.
    Keys can be time-limited or permanent.
    """
    key = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Activation Key"),
        help_text=_("Unique activation key (auto-generated)")
    )
    bunker = models.ForeignKey(
        'bunkers.Bunker',
        on_delete=models.CASCADE,
        related_name='activation_keys',
        verbose_name=_("Bunker")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_keys',
        verbose_name=_("Assigned To"),
        help_text=_("User who can use this key (blank = anyone can use)")
    )
    valid_from = models.DateTimeField(
        verbose_name=_("Valid From"),
        help_text=_("When does this key become valid?")
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Valid Until"),
        help_text=_("When does this key expire? (leave blank for permanent)")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Can this key be used?")
    )
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Maximum Uses"),
        help_text=_("Maximum number of times this key can be used (blank = unlimited)")
    )
    times_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Times Used"),
        help_text=_("How many times has this key been used?")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_keys',
        verbose_name=_("Created By")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Internal notes about this key")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Activation Key")
        verbose_name_plural = _("Activation Keys")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.key} - {self.bunker.reference_number}"

    @staticmethod
    def generate_key(length=12):
        """Generate a random activation key"""
        chars = string.ascii_uppercase + string.digits
        # Remove ambiguous characters
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(length))

    def is_valid_now(self):
        """Check if key is currently valid based on dates, active status, and usage"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from > now:
            return False
        
        if self.valid_until and self.valid_until < now:
            return False
        
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        
        return True

    def can_be_used_by(self, user):
        """Check if a specific user can use this key"""
        if not self.is_valid_now():
            return False
        
        if self.assigned_to and self.assigned_to != user:
            return False
        
        return True

    def use_key(self):
        """Increment usage counter"""
        self.times_used += 1
        self.save(update_fields=['times_used', 'updated_at'])


class ActivationLog(models.Model):
    """
    Log of bunker activations by users.
    Tracks when users activate bunkers and how many QSOs they make.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activations',
        verbose_name=_("User")
    )
    bunker = models.ForeignKey(
        'bunkers.Bunker',
        on_delete=models.CASCADE,
        related_name='activations',
        verbose_name=_("Bunker")
    )
    activation_key = models.ForeignKey(
        'ActivationKey',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activation_logs',
        verbose_name=_("Activation Key"),
        help_text=_("Key used for this activation (if applicable)")
    )
    activator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activator_logs',
        verbose_name=_("Activator"),
        help_text=_("User who was activating the bunker"),
        null=True,
        blank=True
    )
    log_upload = models.ForeignKey(
        'LogUpload',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qsos',
        verbose_name=_("Log Upload"),
        help_text=_("The upload batch this QSO belongs to")
    )
    activation_date = models.DateTimeField(
        verbose_name=_("Activation Date"),
        help_text=_("When did the activation occur?")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("When did the activation end?")
    )
    mode = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name=_("Mode"),
        help_text=_("Radio mode (e.g., SSB, CW, FM, FT8)")
    )
    band = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name=_("Band"),
        help_text=_("Radio band (e.g., 80m, 40m, 2m)")
    )
    qso_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("QSO Count"),
        help_text=_("Number of contacts made during this activation")
    )
    is_b2b = models.BooleanField(
        default=False,
        verbose_name=_("Bunker-to-Bunker (B2B)"),
        help_text=_("Was this a B2B activation?")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes about this activation")
    )
    verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Has this activation been verified?")
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_activations',
        verbose_name=_("Verified By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Activation Log")
        verbose_name_plural = _("Activation Logs")
        ordering = ['-activation_date']
        indexes = [
            models.Index(fields=['user', 'activation_date']),
            models.Index(fields=['bunker', 'activation_date']),
            models.Index(fields=['verified']),
        ]

    def __str__(self):
        return f"{self.user.callsign} activated {self.bunker.reference_number} on {self.activation_date.strftime('%Y-%m-%d')}"

    def get_duration(self):
        """Calculate activation duration if end_date is set"""
        if self.end_date and self.activation_date:
            return self.end_date - self.activation_date
        return None

    def get_duration_hours(self):
        """Get duration in hours"""
        duration = self.get_duration()
        if duration:
            return duration.total_seconds() / 3600
        return None


class License(models.Model):
    """
    Special event licenses or permits for activations.
    Example: Contest licenses, special event callsigns, temporary permits.
    """
    LICENSE_TYPES = [
        ('contest', _('Contest License')),
        ('special_event', _('Special Event')),
        ('temporary', _('Temporary Permit')),
        ('training', _('Training License')),
        ('other', _('Other')),
    ]

    license_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("License Number"),
        help_text=_("Unique license or permit number")
    )
    license_type = models.CharField(
        max_length=20,
        choices=LICENSE_TYPES,
        default='other',
        verbose_name=_("License Type")
    )
    title_pl = models.CharField(
        max_length=200,
        verbose_name=_("Title (Polish)")
    )
    title_en = models.CharField(
        max_length=200,
        verbose_name=_("Title (English)")
    )
    description_pl = models.TextField(
        blank=True,
        verbose_name=_("Description (Polish)")
    )
    description_en = models.TextField(
        blank=True,
        verbose_name=_("Description (English)")
    )
    issued_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='licenses',
        verbose_name=_("Issued To")
    )
    bunkers = models.ManyToManyField(
        'bunkers.Bunker',
        blank=True,
        related_name='licenses',
        verbose_name=_("Authorized Bunkers"),
        help_text=_("Bunkers covered by this license (leave blank for all)")
    )
    valid_from = models.DateTimeField(
        verbose_name=_("Valid From")
    )
    valid_until = models.DateTimeField(
        verbose_name=_("Valid Until")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Is this license currently active?")
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_licenses',
        verbose_name=_("Issued By")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("License")
        verbose_name_plural = _("Licenses")
        ordering = ['-valid_from']

    def __str__(self):
        return f"{self.license_number} - {self.title_en}"

    def is_valid_now(self):
        """Check if license is currently valid"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from > now:
            return False
        
        if self.valid_until < now:
            return False
        
        return True

    def is_valid_for_bunker(self, bunker):
        """Check if license is valid for a specific bunker"""
        if not self.is_valid_now():
            return False
        
        # If no bunkers specified, valid for all
        if not self.bunkers.exists():
            return True
        
        return self.bunkers.filter(pk=bunker.pk).exists()


class LogUpload(models.Model):
    """
    Track log file uploads for audit and history purposes.
    Each upload can contain multiple QSOs/ActivationLogs.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='log_uploads',
        verbose_name=_("User")
    )
    filename = models.CharField(
        max_length=255,
        verbose_name=_("Filename"),
        help_text=_("Original filename of the uploaded log")
    )
    file_format = models.CharField(
        max_length=20,
        verbose_name=_("File Format"),
        help_text=_("Format of the log file (ADIF, CSV, etc.)")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At")
    )
    qso_count = models.IntegerField(
        default=0,
        verbose_name=_("QSO Count"),
        help_text=_("Number of QSOs in this upload")
    )
    processed_qso_count = models.IntegerField(
        default=0,
        verbose_name=_("Processed QSO Count"),
        help_text=_("Number of QSOs successfully processed")
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
        ],
        default='completed',
        verbose_name=_("Status")
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message"),
        help_text=_("Error details if upload failed")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Log Upload")
        verbose_name_plural = _("Log Uploads")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.callsign} - {self.filename} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"
