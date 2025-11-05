from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class DiplomaType(models.Model):
    """
    Types of diplomas that can be earned.
    Examples: Hunter Basic, Hunter Advanced, Activator Bronze, B2B Master, Special Event
    """
    DIPLOMA_CATEGORIES = [
        ('hunter', _('Hunter')),
        ('activator', _('Activator')),
        ('b2b', _('Bunker-to-Bunker')),
        ('special_event', _('Special Event')),
        ('cluster', _('Cluster Achievement')),
        ('other', _('Other')),
    ]

    name_pl = models.CharField(
        max_length=200,
        verbose_name=_("Name (Polish)")
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name=_("Name (English)")
    )
    description_pl = models.TextField(
        verbose_name=_("Description (Polish)")
    )
    description_en = models.TextField(
        verbose_name=_("Description (English)")
    )
    category = models.CharField(
        max_length=20,
        choices=DIPLOMA_CATEGORIES,
        default='other',
        verbose_name=_("Category")
    )
    
    # Point-based requirements
    min_activator_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Activator Points"),
        help_text=_("Each QSO as activator = 1 point")
    )
    min_hunter_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Hunter Points"),
        help_text=_("Each hunted QSO = 1 point")
    )
    min_b2b_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum B2B Points"),
        help_text=_("Each bunker-to-bunker QSO = 1 point")
    )
    
    # Unique bunker requirements (NEW)
    min_unique_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Unique Bunkers Activated"),
        help_text=_("Number of different bunkers activated")
    )
    min_total_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Total Activations"),
        help_text=_("Total number of bunker activations (can repeat same bunker)")
    )
    min_unique_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Unique Bunkers Hunted"),
        help_text=_("Number of different bunkers hunted")
    )
    min_total_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Total Hunted"),
        help_text=_("Total number of bunkers hunted (can repeat same bunker)")
    )
    
    # Date range for special/time-limited diplomas
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid From"),
        help_text=_("Start date for time-limited diploma (leave empty for permanent)")
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid To"),
        help_text=_("End date for time-limited diploma (leave empty for permanent)")
    )
    template_image = models.ImageField(
        upload_to='diploma_templates/',
        blank=True,
        verbose_name=_("Template Image"),
        help_text=_("Background template for PDF generation")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Can this diploma be earned?")
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Diploma Type")
        verbose_name_plural = _("Diploma Types")
        ordering = ['category', 'display_order', 'name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_pl}"

    def get_total_issued(self):
        """Return count of diplomas issued of this type"""
        return self.diplomas.count()
    
    def is_time_limited(self):
        """Check if this is a time-limited diploma"""
        return self.valid_from is not None or self.valid_to is not None
    
    def is_currently_valid(self):
        """Check if diploma can be earned right now (for time-limited diplomas)"""
        if not self.is_time_limited():
            return True
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        
        return True


class Diploma(models.Model):
    """
    Issued diplomas to users.
    Tracks which users have earned which diplomas.
    """
    diploma_type = models.ForeignKey(
        'DiplomaType',
        on_delete=models.PROTECT,
        related_name='diplomas',
        verbose_name=_("Diploma Type")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diplomas',
        verbose_name=_("User")
    )
    issue_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Issue Date")
    )
    diploma_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Diploma Number"),
        help_text=_("Unique diploma certificate number")
    )
    verification_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("Verification Code"),
        help_text=_("UUID for verifying diploma authenticity")
    )
    pdf_file = models.FileField(
        upload_to='diplomas/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_("PDF File")
    )
    
    # Snapshot of points at time of issuance
    activator_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("Activator Points at Issuance")
    )
    hunter_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("Hunter Points at Issuance")
    )
    b2b_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("B2B Points at Issuance")
    )
    
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_diplomas',
        verbose_name=_("Issued By"),
        help_text=_("Admin who issued/approved the diploma")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Diploma")
        verbose_name_plural = _("Diplomas")
        ordering = ['-issue_date']
        unique_together = ['diploma_type', 'user']
        indexes = [
            models.Index(fields=['user', 'issue_date']),
            models.Index(fields=['diploma_number']),
            models.Index(fields=['verification_code']),
        ]

    def __str__(self):
        return f"{self.diploma_number} - {self.user.callsign} - {self.diploma_type.name_en}"

    def save(self, *args, **kwargs):
        """Override save to generate diploma number if not set"""
        if not self.diploma_number:
            self.diploma_number = self.generate_diploma_number(
                self.diploma_type,
                self.user,
                self.issue_date or timezone.now()
            )
        super().save(*args, **kwargs)

    @staticmethod
    def generate_diploma_number(diploma_type, user, issue_date=None):
        """Generate unique diploma number"""
        if issue_date is None:
            issue_date = timezone.now()
        
        # Format: CATEGORY-YYYY-XXXX (e.g., HNT-2025-0001, ACT-2025-0042)
        category_code = {
            'hunter': 'HNT',
            'activator': 'ACT',
            'b2b': 'B2B',
            'special_event': 'SPE',
            'cluster': 'CLU',
            'other': 'OTH'
        }.get(diploma_type.category, 'DIP')
        
        year = issue_date.year
        
        # Count existing diplomas of this type this year
        from django.db import transaction
        with transaction.atomic():
            count = Diploma.objects.select_for_update().filter(
                diploma_type__category=diploma_type.category,
                issue_date__year=year
            ).count() + 1
        
        return f"{category_code}-{year}-{count:04d}"


class DiplomaProgress(models.Model):
    """
    Tracks user progress toward earning diplomas.
    Automatically updated as users complete activities.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diploma_progress',
        verbose_name=_("User")
    )
    diploma_type = models.ForeignKey(
        'DiplomaType',
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_("Diploma Type")
    )
    # Current point totals
    activator_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Activator Points")
    )
    hunter_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Hunter Points")
    )
    b2b_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("B2B Points")
    )
    # Bunker count totals (NEW)
    unique_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Unique Bunkers Activated")
    )
    total_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Activations")
    )
    unique_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Unique Bunkers Hunted")
    )
    total_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Hunted")
    )
    percentage_complete = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Percentage Complete")
    )
    is_eligible = models.BooleanField(
        default=False,
        verbose_name=_("Eligible"),
        help_text=_("Has user met all requirements?")
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated")
    )

    class Meta:
        verbose_name = _("Diploma Progress")
        verbose_name_plural = _("Diploma Progress Records")
        ordering = ['-percentage_complete']
        unique_together = ['user', 'diploma_type']

    def __str__(self):
        return f"{self.user.callsign} - {self.diploma_type.name_en} ({self.percentage_complete}%)"

    def calculate_progress(self):
        """Calculate progress percentage based on all requirements"""
        diploma_type = self.diploma_type
        
        # Check if diploma is time-limited and currently valid
        if diploma_type.is_time_limited() and not diploma_type.is_currently_valid():
            self.percentage_complete = Decimal('0.00')
            self.is_eligible = False
            return Decimal('0.00')
        
        # Collect all requirements
        requirements = {
            'activator_points': (self.activator_points, diploma_type.min_activator_points),
            'hunter_points': (self.hunter_points, diploma_type.min_hunter_points),
            'b2b_points': (self.b2b_points, diploma_type.min_b2b_points),
            'unique_activations': (self.unique_activations, diploma_type.min_unique_activations),
            'total_activations': (self.total_activations, diploma_type.min_total_activations),
            'unique_hunted': (self.unique_hunted, diploma_type.min_unique_hunted),
            'total_hunted': (self.total_hunted, diploma_type.min_total_hunted),
        }
        
        # Calculate progress for each requirement
        percentages = []
        all_met = True
        
        for req_name, (current, required) in requirements.items():
            if required > 0:  # Only count requirements that are set
                pct = min(100, (current / required * 100))
                percentages.append(pct)
                if current < required:
                    all_met = False
        
        # If no requirements are set, diploma is automatically earned
        if not percentages:
            self.percentage_complete = Decimal('100.00')
            self.is_eligible = True
            return Decimal('100.00')
        
        # Calculate average percentage across all requirements
        avg_percentage = sum(percentages) / len(percentages)
        self.percentage_complete = Decimal(str(avg_percentage))
        self.is_eligible = all_met
        
        return self.percentage_complete
    
    def update_points(self, activator=None, hunter=None, b2b=None, 
                      unique_activations=None, total_activations=None,
                      unique_hunted=None, total_hunted=None):
        """Update all progress values and recalculate percentage"""
        if activator is not None:
            self.activator_points = activator
        if hunter is not None:
            self.hunter_points = hunter
        if b2b is not None:
            self.b2b_points = b2b
        if unique_activations is not None:
            self.unique_activations = unique_activations
        if total_activations is not None:
            self.total_activations = total_activations
        if unique_hunted is not None:
            self.unique_hunted = unique_hunted
        if total_hunted is not None:
            self.total_hunted = total_hunted
        
        self.calculate_progress()
        self.save()


class DiplomaVerification(models.Model):
    """
    Log of diploma verification checks.
    Track when and by whom diplomas are verified.
    """
    diploma = models.ForeignKey(
        'Diploma',
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name=_("Diploma")
    )
    verified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Verified At")
    )
    verified_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Verified By IP"),
        help_text=_("IP address of verifier")
    )
    verified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diploma_verifications',
        verbose_name=_("Verified By User"),
        help_text=_("User who performed verification (if logged in)")
    )
    verification_method = models.CharField(
        max_length=50,
        choices=[
            ('number', _('Diploma Number')),
            ('code', _('Verification Code')),
            ('qr', _('QR Code Scan')),
            ('manual', _('Manual Check')),
        ],
        default='number',
        verbose_name=_("Verification Method")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Diploma Verification")
        verbose_name_plural = _("Diploma Verifications")
        ordering = ['-verified_at']

    def __str__(self):
        return f"Verification of {self.diploma.diploma_number} at {self.verified_at.strftime('%Y-%m-%d %H:%M')}"
